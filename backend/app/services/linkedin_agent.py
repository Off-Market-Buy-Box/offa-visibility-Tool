import asyncio
from datetime import datetime
from typing import Callable, Coroutine, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.linkedin_post import LinkedInPost
from app.models.generated_response import GeneratedResponse
from app.services.ai_service import AIService
from app.core.config import settings


class LinkedInAgent:
    """
    Automated agent that:
    1. Picks unprocessed LinkedIn posts
    2. Generates AI responses
    3. Posts them all in ONE browser session (batch mode)
    4. Marks posts as processed
    """

    def __init__(self, delay_between_posts: int = 120):
        self.ai_service = AIService()
        self.delay = delay_between_posts
        self._browser_poster = None

    def _has_credentials(self) -> bool:
        return all([settings.LINKEDIN_EMAIL, settings.LINKEDIN_PASSWORD])

    async def _get_poster(self, db=None):
        from app.core.credentials import get_platform_credentials
        if db:
            creds = await get_platform_credentials("linkedin", db)
            email = creds.get("email", "")
            password = creds.get("password", "")
        else:
            email = settings.LINKEDIN_EMAIL
            password = settings.LINKEDIN_PASSWORD
        if self._browser_poster is None:
            from app.services.linkedin_poster_browser import LinkedInPosterBrowser
            self._browser_poster = LinkedInPosterBrowser(email=email or "", password=password or "")
        return self._browser_poster

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
            "errors": [], "posts": [],
        }

        if not dry_run:
            await emit({"type": "log", "emoji": "🔧", "message": "Checking LinkedIn credentials..."})
            poster = await self._get_poster(db)
            await emit({"type": "log", "emoji": "🤖", "message": "Using browser mode for LinkedIn posting"})
        else:
            await emit({"type": "log", "emoji": "📝", "message": "Dry run mode — will generate but not post"})

        await emit({"type": "log", "emoji": "🔍", "message": "Fetching unprocessed LinkedIn posts..."})
        result = await db.execute(
            select(LinkedInPost)
            .where(LinkedInPost.agent_posted == False)
            .where(LinkedInPost.is_relevant == True)
            .order_by(LinkedInPost.created_at.desc())
            .limit(max_posts)
        )
        threads = result.scalars().all()
        stats["threads_found"] = len(threads)

        if not threads:
            await emit({"type": "log", "emoji": "📭", "message": "No unprocessed LinkedIn posts found"})
            return stats

        await emit({"type": "log", "emoji": "📋", "message": f"Found {len(threads)} posts to process"})

        # Phase 1: Generate all AI responses
        batch_items = []
        for i, thread in enumerate(threads):
            post_info = {
                "id": thread.id, "title": thread.title, "url": thread.url,
                "author": thread.author,
                "content_preview": (thread.content or thread.snippet or "")[:200],
                "status": "pending", "response_content": None, "comment_url": None, "error": None,
            }
            await emit({"type": "post_start", "index": i, "total": len(threads), "post": post_info})

            try:
                await emit({"type": "log", "emoji": "🧠", "message": f"[{i+1}/{len(threads)}] Generating AI response for: {thread.title[:60]}..."})
                response = await self.ai_service.generate_linkedin_response(db, thread.id)
                stats["responses_generated"] += 1
                post_info["response_content"] = response.content
                await emit({"type": "post_response", "index": i, "post_id": thread.id, "response_content": response.content, "char_count": len(response.content)})

                if dry_run:
                    post_info["status"] = "dry_run"
                    stats["posts"].append(post_info)
                    await emit({"type": "post_result", "index": i, "post": post_info})
                else:
                    batch_items.append((thread, post_info, response))
            except Exception as e:
                error_msg = str(e) or repr(e) or "Unknown error"
                stats["errors"].append(f"Post {thread.id}: {error_msg}")
                post_info["status"] = "error"
                post_info["error"] = error_msg
                await emit({"type": "log", "emoji": "❌", "message": f"Error: {error_msg}"})
                await emit({"type": "post_result", "index": i, "post": post_info})
                stats["posts"].append(post_info)

        if dry_run or not batch_items:
            await emit({"type": "log", "emoji": "🏁", "message": f"Done! Generated: {stats['responses_generated']}, Posted: {stats['comments_posted']}, Errors: {len(stats['errors'])}"})
            return stats

        # Phase 2: Post all in one browser session
        await emit({"type": "log", "emoji": "🌐", "message": f"Opening browser — posting {len(batch_items)} comments in one session..."})
        batch_posts = [{"id": t.id, "post_url": t.url, "text": r.content} for t, _, r in batch_items]

        try:
            batch_results = await poster.post_comments_batch(batch_posts, delay_seconds=self.delay)
        except Exception as e:
            for thread, post_info, _ in batch_items:
                post_info["status"] = "error"
                post_info["error"] = str(e)
                stats["errors"].append(f"Post {thread.id}: {str(e)}")
                await emit({"type": "post_result", "index": 0, "post": post_info})
                stats["posts"].append(post_info)
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
                await emit({"type": "log", "emoji": "✅", "message": f"Posted on LinkedIn!"})
            else:
                error_msg = r.get("error", "Unknown batch error")
                stats["errors"].append(f"Post {thread.id}: {error_msg}")
                post_info["status"] = "error"
                post_info["error"] = error_msg
                # Remove from queue so we don't retry unreachable posts forever
                thread.is_relevant = False
                await emit({"type": "log", "emoji": "🗑️", "message": f"Removed from queue (can't comment): {error_msg}"})
            await emit({"type": "post_result", "index": 0, "post": post_info})
            stats["posts"].append(post_info)
        await db.commit()

        await emit({"type": "log", "emoji": "🏁", "message": f"Done! Generated: {stats['responses_generated']}, Posted: {stats['comments_posted']}, Errors: {len(stats['errors'])}"})
        return stats
