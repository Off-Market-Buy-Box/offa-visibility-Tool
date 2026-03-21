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
    3. Posts them to Reddit (via API or browser automation)
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

    async def _get_poster(self):
        if self.mode == "api" or (self.mode == "auto" and self._has_api_credentials()):
            from app.services.reddit_poster import RedditPoster
            return RedditPoster(), "api"

        if self.mode == "browser" or (self.mode == "auto" and self._has_browser_credentials()):
            if self._browser_poster is None:
                from app.services.reddit_poster_browser import RedditPosterBrowser
                self._browser_poster = RedditPosterBrowser()
            return self._browser_poster, "browser"

        raise ValueError(
            "No Reddit credentials configured. Set REDDIT_USERNAME + REDDIT_PASSWORD in .env "
            "(for browser mode) or add REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET (for API mode)."
        )

    async def run(
        self,
        db: AsyncSession,
        max_posts: int = 5,
        dry_run: bool = False,
        on_event: Optional[Callable[[dict], Coroutine]] = None,
    ) -> Dict:
        """
        Run the agent. on_event(event_dict) is called at each step for live updates.
        Event types: "log", "post_start", "post_response", "post_result", "result"
        """
        async def emit(event: dict):
            if on_event:
                await on_event(event)

        stats = {
            "threads_found": 0,
            "responses_generated": 0,
            "comments_posted": 0,
            "errors": [],
            "posts": [],
            "mode": self.mode,
        }

        # Determine posting method
        if not dry_run:
            await emit({"type": "log", "emoji": "🔧", "message": "Checking credentials..."})
            poster, actual_mode = await self._get_poster()
            stats["mode"] = actual_mode
            await emit({"type": "log", "emoji": "🤖", "message": f"Using {actual_mode} mode for posting"})
        else:
            actual_mode = "dry_run"
            await emit({"type": "log", "emoji": "📝", "message": "Dry run mode — will generate but not post"})

        # Get unprocessed threads
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

        for i, thread in enumerate(threads):
            post_info = {
                "id": thread.id,
                "title": thread.title,
                "subreddit": thread.subreddit,
                "url": thread.url,
                "author": thread.author,
                "score": thread.score,
                "num_comments": thread.num_comments,
                "content_preview": (thread.content or "")[:200],
                "status": "pending",
                "response_content": None,
                "comment_url": None,
                "error": None,
            }

            # Emit: starting this post
            await emit({
                "type": "post_start",
                "index": i,
                "total": len(threads),
                "post": post_info,
            })

            try:
                # Step 1: Generate AI response
                await emit({"type": "log", "emoji": "🧠", "message": f"[{i+1}/{len(threads)}] Generating AI response for: {thread.title[:60]}..."})
                response = await self.ai_service.generate_response(db, thread.id)
                stats["responses_generated"] += 1
                post_info["response_content"] = response.content
                post_info["response_preview"] = response.content[:150] + "..."

                # Emit: response generated (full content)
                await emit({
                    "type": "post_response",
                    "index": i,
                    "post_id": thread.id,
                    "response_content": response.content,
                    "char_count": len(response.content),
                })

                if dry_run:
                    post_info["status"] = "dry_run"
                    stats["posts"].append(post_info)
                    await emit({
                        "type": "post_result",
                        "index": i,
                        "post": post_info,
                    })
                    continue

                # Step 2: Post to Reddit
                if actual_mode == "browser":
                    await emit({"type": "log", "emoji": "🌐", "message": "Opening browser & logging in..."})
                await emit({"type": "log", "emoji": "📤", "message": f"Posting to r/{thread.subreddit} via {actual_mode}..."})

                if actual_mode == "api":
                    comment = await poster.post_comment(thread.post_id, response.content)
                else:
                    comment = await poster.post_comment(thread.url, response.content)

                stats["comments_posted"] += 1

                # Step 3: Mark as posted
                thread.agent_posted = True
                thread.agent_posted_at = datetime.utcnow()
                await db.commit()

                post_info["status"] = "posted"
                post_info["comment_url"] = comment.get("comment_url", "")

                await emit({"type": "log", "emoji": "✅", "message": f"Posted to r/{thread.subreddit}!"})
                await emit({
                    "type": "post_result",
                    "index": i,
                    "post": post_info,
                })

            except Exception as e:
                error_msg = str(e) or repr(e) or "Unknown error"
                stats["errors"].append(f"Thread {thread.id}: {error_msg}")
                post_info["status"] = "error"
                post_info["error"] = error_msg

                await emit({"type": "log", "emoji": "❌", "message": f"Error: {error_msg}"})
                await emit({
                    "type": "post_result",
                    "index": i,
                    "post": post_info,
                })

            stats["posts"].append(post_info)

            # Wait between posts
            if not dry_run and thread != threads[-1]:
                await emit({"type": "log", "emoji": "⏳", "message": f"Waiting {self.delay}s before next post..."})
                # Emit countdown updates every 10 seconds
                remaining = self.delay
                while remaining > 0:
                    wait = min(10, remaining)
                    await asyncio.sleep(wait)
                    remaining -= wait
                    if remaining > 0:
                        await emit({"type": "log", "emoji": "⏳", "message": f"{remaining}s remaining..."})

        # Cleanup browser
        if self._browser_poster:
            await emit({"type": "log", "emoji": "🧹", "message": "Closing browser..."})
            await self._browser_poster.close()
            self._browser_poster = None

        await emit({"type": "log", "emoji": "🏁", "message": f"Done! Generated: {stats['responses_generated']}, Posted: {stats['comments_posted']}, Errors: {len(stats['errors'])}"})
        return stats
