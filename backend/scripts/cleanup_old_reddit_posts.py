"""Remove Reddit posts older than 30 days and posts that haven't been commented on"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from sqlalchemy import delete, and_
from app.core.database import AsyncSessionLocal
from app.models.reddit_mention import RedditMention


async def main():
    cutoff = datetime.utcnow() - timedelta(days=30)
    async with AsyncSessionLocal() as db:
        # Delete old uncommented posts
        result = await db.execute(
            delete(RedditMention).where(
                and_(
                    RedditMention.agent_posted == False,
                    RedditMention.posted_at < cutoff,
                )
            )
        )
        deleted = result.rowcount
        await db.commit()
        print(f"✅ Deleted {deleted} old uncommented Reddit posts (older than 30 days)")


if __name__ == "__main__":
    asyncio.run(main())
