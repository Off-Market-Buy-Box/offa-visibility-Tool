import praw
import asyncio
from functools import partial
from typing import Optional
from app.core.config import settings


class RedditPoster:
    """Service for posting comments to Reddit via the official API"""

    def __init__(self):
        self.client_id = settings.REDDIT_CLIENT_ID
        self.client_secret = settings.REDDIT_CLIENT_SECRET
        self.username = settings.REDDIT_USERNAME
        self.password = settings.REDDIT_PASSWORD

    def _get_reddit(self) -> praw.Reddit:
        """Create an authenticated Reddit instance"""
        return praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            username=self.username,
            password=self.password,
            user_agent=f"OffaVisibility/1.0 by /u/{self.username}",
        )

    def _post_comment_sync(self, post_fullname: str, text: str) -> dict:
        """Synchronous method to post a comment"""
        reddit = self._get_reddit()
        submission = reddit.submission(id=post_fullname)
        comment = submission.reply(text)
        return {
            "comment_id": comment.id,
            "comment_url": f"https://www.reddit.com{comment.permalink}",
            "posted": True,
        }

    def _create_post_sync(self, subreddit_name: str, title: str, body: str) -> dict:
        """Synchronous method to create a new text post in a subreddit"""
        reddit = self._get_reddit()
        subreddit = reddit.subreddit(subreddit_name)
        submission = subreddit.submit(title=title, selftext=body)
        return {
            "post_id": submission.id,
            "post_url": f"https://www.reddit.com{submission.permalink}",
            "posted": True,
        }

    async def post_comment(self, post_id: str, text: str) -> dict:
        """Post a comment to a Reddit thread (async wrapper)"""
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            raise ValueError(
                "Reddit API credentials not configured. Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD in .env"
            )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, partial(self._post_comment_sync, post_id, text)
        )
        return result

    async def create_post(self, subreddit: str, title: str, body: str) -> dict:
        """Create a new text post in a subreddit (async wrapper)"""
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            raise ValueError(
                "Reddit API credentials not configured. Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD in .env"
            )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, partial(self._create_post_sync, subreddit, title, body)
        )
        return result

    def _verify_credentials_sync(self) -> dict:
        """Verify Reddit credentials are valid"""
        reddit = self._get_reddit()
        me = reddit.user.me()
        return {
            "authenticated": True,
            "username": me.name,
            "karma": me.comment_karma,
        }

    async def verify_credentials(self) -> dict:
        """Verify Reddit API credentials (async wrapper)"""
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            return {"authenticated": False, "error": "Reddit credentials not configured"}

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._verify_credentials_sync)
            return result
        except Exception as e:
            return {"authenticated": False, "error": str(e)}
