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
    2. Generates AI responses (professional tone with Offa sandwich)
    3. Posts them to LinkedIn via browser automation
    4. Marks posts as processed
    """

    def __init__(self, delay_between_posts: int = 120):
        self.ai_service = AIService()
        self.delay = delay_between_posts
        self._browser_poster = None

    def _has_credentials(self) -> bool:
        return all([settings.LINKEDIN_EMAIL, settings.LINKEDIN_PASSWORD])

    async def _get_poster(self):
        if not self._has_credentials():
            raise ValueError(
                "No LinkedIn credentials configured. "
                "Set LINKEDIN_EMAIL + LINKEDIN_PASSWORD in .env"
            )
        if self._browser_poster is None:
            from app.services.linkedin_poster_browser import LinkedInPosterBrowser
            self._browser_poster = LinkedInPosterBrowser()
        return self._browser_poster

    async def run(
        self,
        db: AsyncSession,
        max_posts: int = 5,
        dry_run: bool = False,
        on_event: Optional[Callable[[dict], Coroutine]] = None,
    ) -> Dict:
        """
        Run the agent. on_event(event_dict) is called at each step for live updates.
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
        }

        if not dry_run:
            await emit({"type": "log", "emoji": "🔧", "message": "Checking LinkedIn credentials..."})
            poster = await self._get_poster()
            await emit({"type": "log", "emoji": "🤖", "message": "Using browser mode for LinkedIn posting"})
        else:
            await emit({"type": "log", "emoji": "📝", "message": "Dry run mode — will generate but not post"})

        # Get unprocessed posts
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

        for i, thread in enumerate(threads):
            post_info = {
                "id": thread.id,
                "title": thread.title,
                "url": thread.url,
                "author": thread.author,
                "content_preview": (thread.content or thread.snippet or "")[:200],
                "status": "pending",
                "response_content": None,
                "comment_url": None,
                "error": None,
            }

            await emit({
                "type": "post_start",
                "index": i,
                "total": len(threads),
                "post": post_info,
            })

            try:
                # Step 1: Generate AI response
                await emit({"type": "log", "emoji": "🧠", "message": f"[{i+1}/{len(threads)}] Generating AI response for: {thread.title[:60]}..."})
                response = await self.ai_service.generate_linkedin_response(db, thread.id)
                stats["responses_generated"] += 1
                post_info["response_content"] = response.content

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
                    await emit({"type": "post_result", "index": i, "post": post_info})
                    continue

                # Step 2: Post to LinkedIn
                await emit({"type": "log", "emoji": "🌐", "message": "Opening browser..."})
                await emit({"type": "log", "emoji": "📤", "message": f"Posting comment on LinkedIn..."})

                comment = await poster.post_comment(thread.url, response.content)
                stats["comments_posted"] += 1

                # Step 3: Mark as posted
                thread.agent_posted = True
                thread.agent_posted_at = datetime.utcnow()
                await db.commit()

                post_info["status"] = "posted"
                post_info["comment_url"] = comment.get("comment_url", "")

                await emit({"type": "log", "emoji": "✅", "message": f"Posted on LinkedIn!"})
                await emit({"type": "post_result", "index": i, "post": post_info})

            except Exception as e:
                error_msg = str(e) or repr(e) or "Unknown error"
                stats["errors"].append(f"Post {thread.id}: {error_msg}")
                post_info["status"] = "error"
                post_info["error"] = error_msg

                await emit({"type": "log", "emoji": "❌", "message": f"Error: {error_msg}"})
                await emit({"type": "post_result", "index": i, "post": post_info})

            stats["posts"].append(post_info)

            # Wait between posts
            if not dry_run and thread != threads[-1]:
                await emit({"type": "log", "emoji": "⏳", "message": f"Waiting {self.delay}s before next post..."})
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
