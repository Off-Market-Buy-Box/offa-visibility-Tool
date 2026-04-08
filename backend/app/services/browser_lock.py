import asyncio


class TimeoutLock:
    """An asyncio lock that never gets stuck.
    
    - acquire() has a timeout — if the lock is held too long, we force-release it
    - The holder is tracked so we can detect stale locks
    """

    def __init__(self, name: str, stale_timeout: int = 660):
        self.name = name
        self._lock = asyncio.Lock()
        self._acquired_at: float = 0
        self._stale_timeout = stale_timeout  # seconds before we consider the lock stale

    async def acquire(self, timeout: int = 300):
        """Try to acquire the lock. If it's stale (held > stale_timeout), force-release it."""
        import time
        deadline = time.monotonic() + timeout
        while True:
            if not self._lock.locked():
                try:
                    # Use wait_for so we don't block forever
                    await asyncio.wait_for(self._lock.acquire(), timeout=5)
                    self._acquired_at = time.monotonic()
                    return True
                except asyncio.TimeoutError:
                    pass

            # Check if the current holder is stale
            if self._lock.locked() and self._acquired_at > 0:
                held_for = time.monotonic() - self._acquired_at
                if held_for > self._stale_timeout:
                    print(f"⚠️ {self.name} lock held for {held_for:.0f}s — force releasing stale lock")
                    self._force_release()
                    continue

            if time.monotonic() >= deadline:
                print(f"⏰ {self.name} lock acquire timed out after {timeout}s")
                return False

            await asyncio.sleep(1)

    def release(self):
        try:
            if self._lock.locked():
                self._lock.release()
                self._acquired_at = 0
        except RuntimeError:
            pass  # already released

    def _force_release(self):
        """Force-release a stuck lock."""
        try:
            if self._lock.locked():
                self._lock.release()
                self._acquired_at = 0
        except RuntimeError:
            # If it's truly stuck, replace the lock entirely
            self._lock = asyncio.Lock()
            self._acquired_at = 0

    @property
    def locked(self):
        return self._lock.locked()


# One lock for Reddit browser (shared between commenting and outreach posting)
reddit_browser_lock = TimeoutLock("reddit_browser", stale_timeout=660)
