import asyncio
from datetime import datetime
from typing import Dict, Optional
from app.core.database import AsyncSessionLocal
from app.models.outreach_target import OutreachTarget, OutreachPost
from sqlalchemy import select


class OutreachService:
    """Background loop: generates AI posts and submits to subreddits daily"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._status: Dict = {
            "running": False,
            "last_run_at": None,
            "next_run_at": None,
            "total_posted": 0,
            "total_errors": 0,
            "current_action": None,
            "interval_hours": 24,
        }

    def get_status(self) -> Dict:
        return {**self._status, "running": self._running}

    def update_settings(self, settings: Dict):
        if "interval_hours" in settings:
            self._status["interval_hours"] = max(1, min(168, settings["interval_hours"]))

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._status["current_action"] = None

    async def _loop(self):
        while self._running:
            self._status["current_action"] = "posting to subreddits"
            await self._run_cycle()

            self._status["last_run_at"] = datetime.utcnow().isoformat()
            interval_secs = self._status["interval_hours"] * 3600
            next_run = datetime.utcnow().timestamp() + interval_secs
            self._status["next_run_at"] = datetime.utcfromtimestamp(next_run).isoformat()
            self._status["current_action"] = f"waiting {self._status['interval_hours']}h until next cycle"

            await self._sleep(interval_secs)

        self._status["current_action"] = None

    async def _run_cycle(self, raise_errors=False):
        """Post to all enabled subreddits that haven't been posted to today"""
        # Track whether we were called manually (not from background loop)
        is_manual = not self._running
        try:
            async with AsyncSessionLocal() as db:
                from app.services.ai_service import AIService
                from app.services.reddit_poster_browser import RedditPosterBrowser
                from app.core.credentials import get_platform_credentials

                ai = AIService()
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

                result = await db.execute(
                    select(OutreachTarget).where(OutreachTarget.enabled == True)
                )
                targets = result.scalars().all()

                if not targets:
                    print("📭 No enabled outreach targets")
                    if raise_errors:
                        raise RuntimeError("No enabled outreach targets. Add subreddits and enable them first.")
                    return

                creds = await get_platform_credentials("reddit", db)
                poster = RedditPosterBrowser(
                    username=creds.get("username", ""),
                    password=creds.get("password", ""),
                )

                for target in targets:
                    # Only check _running for background loop, not manual runs
                    if not is_manual and not self._running:
                        break

                    if target.last_posted_at and target.last_posted_at >= today:
                        print(f"⏭️ Skipping {target.name} — already posted today")
                        continue

                    subreddit = target.url.rstrip("/").split("/r/")[-1].split("/")[0]
                    self._status["current_action"] = f"generating post for {target.name}"
                    print(f"🤖 Generating AI post for {target.name}...")

                    # Get past titles for this target to avoid repetition
                    past_result = await db.execute(
                        select(OutreachPost.title)
                        .where(OutreachPost.target_id == target.id)
                        .where(OutreachPost.title.isnot(None))
                        .order_by(OutreachPost.created_at.desc())
                        .limit(20)
                    )
                    past_titles = [r[0] for r in past_result.all() if r[0]]

                    try:
                        post_data = await ai.generate_reddit_outreach_post(
                            subreddit=subreddit, past_titles=past_titles
                        )
                        title = post_data["title"]
                        body = post_data["body"]

                        post = OutreachPost(
                            target_id=target.id, platform="reddit",
                            title=title, content=body, status="pending",
                        )
                        db.add(post)
                        await db.flush()

                        self._status["current_action"] = f"posting to {target.name}"
                        print(f"📤 Posting to {target.name}: {title}")

                        await poster.create_post(subreddit, title, body)

                        post.status = "posted"
                        post.posted_at = datetime.utcnow()
                        target.last_posted_at = datetime.utcnow()
                        target.total_posts += 1
                        self._status["total_posted"] += 1
                        print(f"✅ Posted to {target.name}")

                    except Exception as e:
                        print(f"❌ Error posting to {target.name}: {e}")
                        import traceback
                        traceback.print_exc()
                        self._status["total_errors"] += 1
                        try:
                            post.status = "error"
                            post.error = str(e)
                        except Exception:
                            pass
                        if raise_errors:
                            await db.commit()
                            raise

                    await db.commit()

                    # Wait between posts to avoid rate limits (only in background loop)
                    if not is_manual and self._running:
                        self._status["current_action"] = "waiting 60s between posts"
                        await self._sleep(60)

        except Exception as e:
            if raise_errors:
                raise
            print(f"❌ Outreach cycle error: {e}")
            import traceback
            traceback.print_exc()
            self._status["total_errors"] += 1

    async def _sleep(self, seconds):
        """Interruptible sleep"""
        for _ in range(int(seconds)):
            if not self._running:
                return
            await asyncio.sleep(1)


# Singleton
outreach_automation = OutreachService()
