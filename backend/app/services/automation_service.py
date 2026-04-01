import asyncio
from datetime import datetime
from typing import Dict, Optional
from app.core.database import AsyncSessionLocal
from app.models.automation_log import AutomationLog


class AutomationService:
    """Continuous loop: scan → comment → next platform → repeat"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._status: Dict = {
            "running": False,
            "current_platform": None,
            "current_action": None,
            "cycle_count": 0,
            "last_cycle_at": None,
            "platforms": {
                "reddit": {"enabled": True, "last_scan": None, "last_comment": None, "total_commented": 0, "total_scanned": 0, "errors": 0},
                "linkedin": {"enabled": True, "last_scan": None, "last_comment": None, "total_commented": 0, "total_scanned": 0, "errors": 0},
                "twitter": {"enabled": True, "last_scan": None, "last_comment": None, "total_commented": 0, "total_scanned": 0, "errors": 0},
                "facebook": {"enabled": True, "last_scan": None, "last_comment": None, "total_commented": 0, "total_scanned": 0, "errors": 0},
            },
            "delay_between_cycles": 10,
            "max_posts_per_run": 10,
        }

    def get_status(self) -> Dict:
        return {**self._status, "running": self._running}

    def update_settings(self, settings: Dict):
        for key in ["delay_between_cycles", "max_posts_per_run"]:
            if key in settings:
                self._status[key] = settings[key]
        if "platforms" in settings:
            for platform, config in settings["platforms"].items():
                if platform in self._status["platforms"]:
                    self._status["platforms"][platform]["enabled"] = config.get("enabled", True)

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
        self._status["current_platform"] = None
        self._status["current_action"] = None

    async def _has_pending_posts(self, platform: str) -> bool:
        """Check if there are uncommented posts in the DB for this platform"""
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, func
                if platform == "reddit":
                    from app.models.reddit_mention import RedditMention as Model
                elif platform == "linkedin":
                    from app.models.linkedin_post import LinkedInPost as Model
                elif platform == "twitter":
                    from app.models.twitter_post import TwitterPost as Model
                elif platform == "facebook":
                    from app.models.facebook_post import FacebookPost as Model
                else:
                    return False

                result = await db.execute(
                    select(func.count(Model.id))
                    .where(Model.agent_posted == False)
                    .where(Model.is_relevant == True)
                )
                count = result.scalar() or 0
                return count > 0
        except Exception:
            return False

    async def _loop(self):
        platforms = ["reddit", "linkedin", "twitter", "facebook"]
        while self._running:
            self._status["cycle_count"] += 1
            had_work = False

            for platform in platforms:
                if not self._running:
                    break
                if not self._status["platforms"][platform]["enabled"]:
                    continue

                self._status["current_platform"] = platform

                # Only scan if no pending posts
                has_pending = await self._has_pending_posts(platform)
                if not has_pending:
                    self._status["current_action"] = "scanning"
                    await self._scan(platform)
                    if not self._running:
                        break

                # Comment on pending posts
                self._status["current_action"] = "commenting"
                result = await self._comment(platform)
                if result.get("comments_posted", 0) > 0:
                    had_work = True

                if not self._running:
                    break

            self._status["current_platform"] = None
            self._status["last_cycle_at"] = datetime.utcnow().isoformat()

            if had_work:
                self._status["current_action"] = "short pause before next cycle"
                await self._sleep(30)
            else:
                self._status["current_action"] = "waiting between cycles"
                await self._sleep(self._status["delay_between_cycles"])

        self._status["current_action"] = None

    async def _sleep(self, seconds: int):
        """Interruptible sleep"""
        for _ in range(seconds):
            if not self._running:
                return
            await asyncio.sleep(1)

    async def _scan(self, platform: str) -> Dict:
        try:
            async with AsyncSessionLocal() as db:
                if platform == "reddit":
                    from app.services.reddit_service import RedditService
                    svc = RedditService()
                    stats = await svc.monitor_real_estate_mentions(db)
                    found = stats.get("total_mentions_found", 0)
                elif platform == "linkedin":
                    from app.services.linkedin_service import LinkedInService
                    svc = LinkedInService()
                    stats = await svc.monitor_linkedin(db)
                    found = stats.get("total_found", 0)
                elif platform == "twitter":
                    from app.services.twitter_service import TwitterService
                    svc = TwitterService()
                    stats = await svc.monitor_twitter(db)
                    found = stats.get("total_found", 0)
                elif platform == "facebook":
                    from app.services.facebook_service import FacebookService
                    svc = FacebookService()
                    stats = await svc.monitor_facebook(db)
                    found = stats.get("total_found", 0)
                else:
                    return {}

                self._status["platforms"][platform]["last_scan"] = datetime.utcnow().isoformat()
                self._status["platforms"][platform]["total_scanned"] += found

                log = AutomationLog(
                    platform=platform, action="scan",
                    posts_found=found, posts_commented=0, errors=0,
                    details=stats,
                )
                db.add(log)
                await db.commit()
                return stats
        except Exception as e:
            self._status["platforms"][platform]["errors"] += 1
            try:
                async with AsyncSessionLocal() as db:
                    log = AutomationLog(
                        platform=platform, action="scan",
                        posts_found=0, posts_commented=0, errors=1,
                        details={"error": str(e)},
                    )
                    db.add(log)
                    await db.commit()
            except Exception:
                pass
            return {"error": str(e)}

    async def _comment(self, platform: str) -> Dict:
        try:
            async with AsyncSessionLocal() as db:
                max_posts = self._status["max_posts_per_run"]
                commented_count = 0
                error_count = 0

                async def on_event(event: dict):
                    nonlocal commented_count, error_count
                    if event.get("type") == "post_result":
                        post = event.get("post", {})
                        if post.get("status") == "posted":
                            commented_count += 1
                            self._status["platforms"][platform]["total_commented"] += 1
                            self._status["platforms"][platform]["last_comment"] = datetime.utcnow().isoformat()
                            # Log each successful comment immediately
                            try:
                                async with AsyncSessionLocal() as log_db:
                                    log = AutomationLog(
                                        platform=platform, action="comment",
                                        posts_found=0, posts_commented=1, errors=0,
                                        details={"title": post.get("title", ""), "url": post.get("url", "")},
                                    )
                                    log_db.add(log)
                                    await log_db.commit()
                            except Exception:
                                pass
                        elif post.get("status") == "error":
                            error_count += 1

                if platform == "reddit":
                    from app.services.reddit_agent import RedditAgent
                    agent = RedditAgent(delay_between_posts=30)
                    stats = await agent.run(db, max_posts=max_posts, on_event=on_event)
                elif platform == "linkedin":
                    from app.services.linkedin_agent import LinkedInAgent
                    agent = LinkedInAgent(delay_between_posts=30)
                    stats = await agent.run(db, max_posts=max_posts, on_event=on_event)
                elif platform == "twitter":
                    from app.services.twitter_agent import TwitterAgent
                    agent = TwitterAgent(delay_between_posts=30)
                    stats = await agent.run(db, max_posts=max_posts, on_event=on_event)
                elif platform == "facebook":
                    from app.services.facebook_agent import FacebookAgent
                    agent = FacebookAgent(delay_between_posts=30)
                    stats = await agent.run(db, max_posts=max_posts, on_event=on_event)
                else:
                    return {}

                return stats
        except Exception as e:
            self._status["platforms"][platform]["errors"] += 1
            try:
                async with AsyncSessionLocal() as log_db:
                    log = AutomationLog(
                        platform=platform, action="comment",
                        posts_found=0, posts_commented=0, errors=1,
                        details={"error": str(e)},
                    )
                    log_db.add(log)
                    await log_db.commit()
            except Exception:
                pass
            return {"error": str(e)}


# Singleton
automation = AutomationService()
