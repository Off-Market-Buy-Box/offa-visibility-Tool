import asyncio
import os
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.core.database import AsyncSessionLocal
from app.models.automation_log import AutomationLog


# Rate limits per platform
RATE_LIMITS = {
    "reddit": {
        "delay_between_posts": 600,   # 10 minutes between comments
        "daily_limit": None,           # No daily cap, just time-gated
        "max_per_run": 1,              # 1 at a time due to 10min gap
    },
    "linkedin": {
        "delay_between_posts": 120,
        "daily_limit": 30,
        "max_per_run": 5,
    },
    "twitter": {
        "delay_between_posts": 60,
        "daily_limit": 100,
        "max_per_run": 10,
    },
    "facebook": {
        "delay_between_posts": 120,
        "daily_limit": 50,
        "max_per_run": 5,
    },
}

# Max consecutive failures before temporarily skipping a platform
MAX_CONSECUTIVE_FAILURES = 3
FAILURE_COOLDOWN_SECONDS = 600  # 10 min cooldown after too many failures


class AutomationService:
    """Continuous loop: scan → comment → next platform → repeat (with rate limits)"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._comment_timestamps: Dict[str, List[datetime]] = {
            "reddit": [], "linkedin": [], "twitter": [], "facebook": [],
        }
        # Track active subprocess PIDs so we can kill them on stop
        self._active_pids: List[int] = []
        # Track consecutive failures per platform
        self._consecutive_failures: Dict[str, int] = {
            "reddit": 0, "linkedin": 0, "twitter": 0, "facebook": 0,
        }
        self._platform_cooldown_until: Dict[str, Optional[datetime]] = {
            "reddit": None, "linkedin": None, "twitter": None, "facebook": None,
        }
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

    def register_pid(self, pid: int):
        """Register a subprocess PID for cleanup on stop"""
        self._active_pids.append(pid)

    def unregister_pid(self, pid: int):
        """Remove a subprocess PID after it finishes"""
        if pid in self._active_pids:
            self._active_pids.remove(pid)

    def _kill_all_subprocesses(self):
        """Force-kill all tracked browser subprocesses"""
        for pid in list(self._active_pids):
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"🔪 Killed subprocess PID {pid}")
            except (OSError, ProcessLookupError):
                pass
        self._active_pids.clear()

    def _prune_old_timestamps(self, platform: str):
        """Remove timestamps older than 24h"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._comment_timestamps[platform] = [
            ts for ts in self._comment_timestamps[platform] if ts > cutoff
        ]

    def _get_count_last_24h(self, platform: str) -> int:
        self._prune_old_timestamps(platform)
        return len(self._comment_timestamps[platform])

    def _record_comment(self, platform: str, amount: int = 1):
        now = datetime.utcnow()
        for _ in range(amount):
            self._comment_timestamps[platform].append(now)

    def _can_comment(self, platform: str) -> bool:
        """Check if we're within rate limits for this platform"""
        limits = RATE_LIMITS.get(platform, {})
        daily_limit = limits.get("daily_limit")
        if daily_limit is not None:
            if self._get_count_last_24h(platform) >= daily_limit:
                return False
        return True

    def _is_platform_in_cooldown(self, platform: str) -> bool:
        """Check if platform is in failure cooldown"""
        until = self._platform_cooldown_until.get(platform)
        if until and datetime.utcnow() < until:
            return True
        if until and datetime.utcnow() >= until:
            # Cooldown expired, reset
            self._platform_cooldown_until[platform] = None
            self._consecutive_failures[platform] = 0
        return False

    def _record_failure(self, platform: str):
        """Record a failure and enter cooldown if too many"""
        self._consecutive_failures[platform] += 1
        if self._consecutive_failures[platform] >= MAX_CONSECUTIVE_FAILURES:
            self._platform_cooldown_until[platform] = (
                datetime.utcnow() + timedelta(seconds=FAILURE_COOLDOWN_SECONDS)
            )
            print(f"⏸️ {platform}: {MAX_CONSECUTIVE_FAILURES} consecutive failures, cooling down for {FAILURE_COOLDOWN_SECONDS}s")

    def _record_success(self, platform: str):
        """Reset failure counter on success"""
        self._consecutive_failures[platform] = 0
        self._platform_cooldown_until[platform] = None

    def _get_remaining_24h(self, platform: str) -> Optional[int]:
        """How many comments left in the rolling 24h window"""
        limits = RATE_LIMITS.get(platform, {})
        daily_limit = limits.get("daily_limit")
        if daily_limit is None:
            return None
        return max(0, daily_limit - self._get_count_last_24h(platform))

    def get_status(self) -> Dict:
        status = {**self._status, "running": self._running}
        status["rate_limits"] = {}
        for p in ["reddit", "linkedin", "twitter", "facebook"]:
            limits = RATE_LIMITS.get(p, {})
            remaining = self._get_remaining_24h(p)
            cooldown = self._platform_cooldown_until.get(p)
            status["rate_limits"][p] = {
                "daily_limit": limits.get("daily_limit"),
                "used_24h": self._get_count_last_24h(p),
                "remaining_24h": remaining,
                "delay_between_posts": limits.get("delay_between_posts", 60),
                "in_cooldown": self._is_platform_in_cooldown(p),
                "cooldown_until": cooldown.isoformat() if cooldown else None,
                "consecutive_failures": self._consecutive_failures.get(p, 0),
            }
        return status

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
        # Kill any running browser subprocesses immediately
        self._kill_all_subprocesses()
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

                # Check failure cooldown
                if self._is_platform_in_cooldown(platform):
                    cooldown = self._platform_cooldown_until.get(platform)
                    remaining = int((cooldown - datetime.utcnow()).total_seconds()) if cooldown else 0
                    print(f"⏸️ {platform}: in cooldown ({remaining}s remaining), skipping")
                    self._status["current_action"] = f"cooldown ({remaining}s)"
                    continue

                # Check daily rate limit before doing anything
                if not self._can_comment(platform):
                    print(f"⏸️ {platform}: 24h limit reached ({RATE_LIMITS[platform].get('daily_limit')} comments), skipping")
                    self._status["current_action"] = "24h limit reached"
                    continue

                # Only scan if no pending posts
                has_pending = await self._has_pending_posts(platform)
                if not has_pending:
                    self._status["current_action"] = "scanning"
                    try:
                        scan_result = await self._scan(platform)
                    except Exception as e:
                        print(f"❌ {platform} scan error: {e}")
                        self._record_failure(platform)
                        continue
                    if not self._running:
                        break

                    has_pending = await self._has_pending_posts(platform)
                    if not has_pending:
                        continue

                # Comment on pending posts (respecting rate limits)
                self._status["current_action"] = "commenting"
                limits = RATE_LIMITS.get(platform, {})
                max_per_run = limits.get("max_per_run", 5)
                delay = limits.get("delay_between_posts", 60)

                # Cap by remaining 24h allowance
                remaining = self._get_remaining_24h(platform)
                if remaining is not None:
                    max_per_run = min(max_per_run, remaining)

                if max_per_run <= 0:
                    continue

                try:
                    result = await self._comment(platform, max_posts=max_per_run, delay=delay)
                    posted = result.get("comments_posted", 0)
                    errors = len(result.get("errors", []))

                    if posted > 0:
                        self._record_comment(platform, posted)
                        self._record_success(platform)
                        had_work = True
                    elif errors > 0 and posted == 0:
                        # All posts in this run failed
                        self._record_failure(platform)
                    else:
                        # No posts found to comment on
                        self._record_success(platform)

                except Exception as e:
                    print(f"❌ {platform} comment error: {e}")
                    self._record_failure(platform)

                if not self._running:
                    break

            self._status["current_platform"] = None
            self._status["last_cycle_at"] = datetime.utcnow().isoformat()

            if had_work:
                self._status["current_action"] = "short pause before next cycle"
                await self._sleep(30)
            else:
                self._status["current_action"] = "waiting between cycles"
                await self._sleep(max(self._status["delay_between_cycles"], 60))

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
                    new_saved = stats.get("new_mentions_saved", found)
                elif platform == "linkedin":
                    from app.services.linkedin_service import LinkedInService
                    svc = LinkedInService()
                    stats = await svc.monitor_linkedin(db)
                    found = stats.get("total_found", 0)
                    new_saved = stats.get("new_saved", found)
                elif platform == "twitter":
                    from app.services.twitter_service import TwitterService
                    svc = TwitterService()
                    stats = await svc.monitor_twitter(db)
                    found = stats.get("total_found", 0)
                    new_saved = stats.get("new_saved", found)
                elif platform == "facebook":
                    from app.services.facebook_service import FacebookService
                    svc = FacebookService()
                    stats = await svc.monitor_facebook(db)
                    found = stats.get("total_found", 0)
                    new_saved = stats.get("new_saved", found)
                else:
                    return {}

                self._status["platforms"][platform]["last_scan"] = datetime.utcnow().isoformat()
                self._status["platforms"][platform]["total_scanned"] += new_saved

                log = AutomationLog(
                    platform=platform, action="scan",
                    posts_found=new_saved, posts_commented=0, errors=0,
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

    async def _comment(self, platform: str, max_posts: int = 5, delay: int = 60) -> Dict:
        try:
            async with AsyncSessionLocal() as db:
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
                    agent = RedditAgent(delay_between_posts=delay)
                    stats = await agent.run(db, max_posts=max_posts, on_event=on_event)
                elif platform == "linkedin":
                    from app.services.linkedin_agent import LinkedInAgent
                    agent = LinkedInAgent(delay_between_posts=delay)
                    stats = await agent.run(db, max_posts=max_posts, on_event=on_event)
                elif platform == "twitter":
                    from app.services.twitter_agent import TwitterAgent
                    agent = TwitterAgent(delay_between_posts=delay)
                    stats = await agent.run(db, max_posts=max_posts, on_event=on_event)
                elif platform == "facebook":
                    from app.services.facebook_agent import FacebookAgent
                    agent = FacebookAgent(delay_between_posts=delay)
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
