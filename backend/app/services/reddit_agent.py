import asyncio
from datetime import datetime
from typing import AsyncGenerator, Callable, Coroutine, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.reddit_mention import RedditMention
from app.models.generated_response import GeneratedResponse
from app.services.ai_service import AIService
from app.core.config import settings


class RedditAgent:
    """
    Automated agent that:
    1. Picks unprocessed Reddit threads
    2. Generates AI responses (with Offa sandwich technique)
    3. Posts them all in ONE browser session (batch mode)
    4. Marks threads as processed
    """

    def __init__(self, delay_between_posts: int = 120, mode: str = "auto"):
        self.ai_service = AIService()
        self.delay = delay_between_posts
        self.mode = mode
        self._browser_poster = None

    def _has_api_credentials(self) -> bool:
        return all([
            settings.REDDIT_CLIENT_ID,
            settings.REDDIT_CLIENT_SECRET,
            settings.REDDIT_USERNAME,
            settings.REDDIT_PASSWORD,
        ])

    def _has_browser_credentials(self) -> bool:
        return all([settings.REDDIT_USERNAME, settings.REDDIT_PASSWORD])

    async def _get_poster(self, db=None):
        from app.core.credentials import get_platform_credentials
        if db:
            creds = await get_platform_credentials("reddit", db)
            username = creds.get("username", "")
            password = creds.get("password", "")
        else:
            username = settings.REDDIT_USERNAME
            password = settings.REDDIT_PASSWORD

        if self.mode == "api" or (self.mode == "auto" and self._has_api_credentials()):
            from app.services.reddit_poster import RedditPoster
            return RedditPoster(), "api"

        # Browser mode — session may already be saved, credentials optional
        if self._browser_poster is None:
            from app.services.reddit_poster_browser import RedditPosterBrowser
            self._browser_poster = RedditPosterBrowser(username=username or "", password=password or "")
        return self._browser_poster, "browser"

    async def run(
        self,
        db: AsyncSession,
        max_posts: int = 5,
        dry_run: bool = False,
        on_event: Optional[Callable[[dict], Coroutine]] = None,
    ) -> Dict:
        """Run the agent. Opens ONE browser, posts all comments, then closes."""
        async def emit(event: dict):
            if on_event:
                await on_event(event)

        stats = {
            "threads_found": 0, "responses_generated": 0, "comments_posted": 0,
            "errors": [], "posts": [], "mode": self.mode,
        }

        if not dry_run:
            await emit({"type": "log", "emoji": "🔧", "message": "Checking credentials..."})
            poster, actual_mode = await self._get_poster(db)
            stats["mode"] = actual_mode
            await emit({"type": "log", "emoji": "🤖", "message": f"Using {actual_mode} mode for posting"})
        else:
            actual_mode = "dry_run"
            await emit({"type": "log", "emoji": "📝", "message": "Dry run mode — will generate but not post"})

        await emit({"type": "log", "emoji": "🔍", "message": "Fetching unprocessed threads..."})
        result = await db.execute(
            select(RedditMention)
            .where(RedditMention.agent_posted == False)
            .where(RedditMention.is_relevant == True)
            .order_by(RedditMention.created_at.desc())
            .limit(max_posts)
        )
        threads = result.scalars().all()
        stats["threads_found"] = len(threads)

        if not threads:
            await emit({"type": "log", "emoji": "📭", "message": "No unprocessed threads found"})
            return stats

        await emit({"type": "log", "emoji": "📋", "message": f"Found {len(threads)} threads to process"})

        # Phase 1: Generate all AI responses
        batch_items = []
        for i, thread in enumerate(threads):
            post_info = {
                "id": thread.id, "title": thread.title, "subreddit": thread.subreddit,
                "url": thread.url, "author": thread.author, "score": thread.score,
                "num_comments": thread.num_comments,
                "content_preview": (thread.content or "")[:200],
                "status": "pending", "response_content": None, "comment_url": None, "error": None,
            }
            await emit({"type": "post_start", "index": i, "total": len(threads), "post": post_info})

            try:
                await emit({"type": "log", "emoji": "🧠", "message": f"[{i+1}/{len(threads)}] Generating AI response for: {thread.title[:60]}..."})
                response = await self.ai_service.generate_response(db, thread.id)
                stats["responses_generated"] += 1
                post_info["response_content"] = response.content
                post_info["response_preview"] = response.content[:150] + "..."
                await emit({"type": "post_response", "index": i, "post_id": thread.id, "response_content": response.content, "char_count": len(response.content)})

                if dry_run:
                    post_info["status"] = "dry_run"
                    stats["posts"].append(post_info)
                    await emit({"type": "post_result", "index": i, "post": post_info})
                else:
                    batch_items.append((thread, post_info, response))
            except Exception as e:
                error_msg = str(e) or repr(e) or "Unknown error"
                stats["errors"].append(f"Thread {thread.id}: {error_msg}")
                post_info["status"] = "error"
                post_info["error"] = error_msg
                await emit({"type": "log", "emoji": "❌", "message": f"Error: {error_msg}"})
                await emit({"type": "post_result", "index": i, "post": post_info})
                stats["posts"].append(post_info)

        if dry_run or not batch_items:
            await emit({"type": "log", "emoji": "🏁", "message": f"Done! Generated: {stats['responses_generated']}, Posted: {stats['comments_posted']}, Errors: {len(stats['errors'])}"})
            return stats

        # Phase 2: Post all in one browser session (batch)
        if actual_mode == "browser" and hasattr(poster, 'post_comments_batch'):
            await emit({"type": "log", "emoji": "🌐", "message": f"Opening browser — posting {len(batch_items)} comments in one session..."})
            batch_posts = [{"id": t.id, "post_url": t.url, "text": r.content} for t, _, r in batch_items]

            try:
                batch_results = await poster.post_comments_batch(batch_posts, delay_seconds=self.delay)
            except Exception as e:
                error_msg = str(e)
                is_timeout = "timed out" in error_msg.lower() or "timeout" in error_msg.lower()
                for thread, post_info, _ in batch_items:
                    post_info["status"] = "error"
                    post_info["error"] = error_msg
                    stats["errors"].append(f"Thread {thread.id}: {error_msg}")
                    if not is_timeout:
                        thread.is_relevant = False
                    await emit({"type": "post_result", "index": 0, "post": post_info})
                    stats["posts"].append(post_info)
                if not is_timeout:
                    await db.commit()
                await emit({"type": "log", "emoji": "🏁", "message": f"Done! Generated: {stats['responses_generated']}, Posted: 0, Errors: {len(stats['errors'])}"})
                return stats

            result_map = {r.get("id"): r for r in batch_results}
            for thread, post_info, _ in batch_items:
                r = result_map.get(thread.id, {})
                if r.get("posted"):
                    stats["comments_posted"] += 1
                    thread.agent_posted = True
                    thread.agent_posted_at = datetime.utcnow()
                    post_info["status"] = "posted"
                    post_info["comment_url"] = r.get("comment_url", "")
                    await emit({"type": "log", "emoji": "✅", "message": f"Posted to r/{thread.subreddit}!"})
                else:
                    error_msg = r.get("error", "Unknown batch error")
                    stats["errors"].append(f"Thread {thread.id}: {error_msg}")
                    post_info["status"] = "error"
                    post_info["error"] = error_msg
                    # Remove from queue so we don't retry unreachable posts forever
                    thread.is_relevant = False
                    await emit({"type": "log", "emoji": "🗑️", "message": f"Removed from queue (can't comment): {error_msg}"})
                await emit({"type": "post_result", "index": 0, "post": post_info})
                stats["posts"].append(post_info)
            await db.commit()
        else:
            # API mode fallback: post one by one
            for i, (thread, post_info, response) in enumerate(batch_items):
                try:
                    await emit({"type": "log", "emoji": "📤", "message": f"Posting to r/{thread.subreddit} via {actual_mode}..."})
                    if actual_mode == "api":
                        comment = await poster.post_comment(thread.post_id, response.content)
                    else:
                        comment = await poster.post_comment(thread.url, response.content)
                    stats["comments_posted"] += 1
                    thread.agent_posted = True
                    thread.agent_posted_at = datetime.utcnow()
                    await db.commit()
                    post_info["status"] = "posted"
                    post_info["comment_url"] = comment.get("comment_url", "")
                    await emit({"type": "log", "emoji": "✅", "message": f"Posted to r/{thread.subreddit}!"})
                except Exception as e:
                    error_msg = str(e) or repr(e) or "Unknown error"
                    stats["errors"].append(f"Thread {thread.id}: {error_msg}")
                    post_info["status"] = "error"
                    post_info["error"] = error_msg
                    # Remove from queue so we don't retry unreachable posts forever
                    thread.is_relevant = False
                    await db.commit()
                    await emit({"type": "log", "emoji": "🗑️", "message": f"Removed from queue (can't comment): {error_msg}"})
                await emit({"type": "post_result", "index": i, "post": post_info})
                stats["posts"].append(post_info)
                if thread != batch_items[-1][0]:
                    await emit({"type": "log", "emoji": "⏳", "message": f"Waiting {self.delay}s..."})
                    remaining = self.delay
                    while remaining > 0:
                        wait = min(10, remaining)
                        await asyncio.sleep(wait)
                        remaining -= wait

        await emit({"type": "log", "emoji": "🏁", "message": f"Done! Generated: {stats['responses_generated']}, Posted: {stats['comments_posted']}, Errors: {len(stats['errors'])}"})
        return stats
