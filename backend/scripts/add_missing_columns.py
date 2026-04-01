"""
Add all missing columns to existing tables.
Safe to run multiple times — skips columns that already exist.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

# Import all models
from app.models.keyword import Keyword
from app.models.ranking import Ranking
from app.models.competitor import Competitor
from app.models.reddit_mention import RedditMention
from app.models.smart_task import SmartTask
from app.models.linkedin_post import LinkedInPost
from app.models.twitter_post import TwitterPost
from app.models.facebook_post import FacebookPost
from app.models.ai_metadata import AIMetadata
from app.models.generated_response import GeneratedResponse
from app.models.platform_credential import PlatformCredential
from app.models.automation_log import AutomationLog
from app.core.database import Base


COLUMNS_TO_ADD = [
    # linkedin_posts
    ("linkedin_posts", "agent_posted", "BOOLEAN DEFAULT FALSE"),
    ("linkedin_posts", "agent_posted_at", "TIMESTAMP"),
    # twitter_posts
    ("twitter_posts", "agent_posted", "BOOLEAN DEFAULT FALSE"),
    ("twitter_posts", "agent_posted_at", "TIMESTAMP"),
    # reddit_mentions
    ("reddit_mentions", "agent_posted", "BOOLEAN DEFAULT FALSE"),
    ("reddit_mentions", "agent_posted_at", "TIMESTAMP"),
    # ai_metadata
    ("ai_metadata", "twitter_post_id", "INTEGER REFERENCES twitter_posts(id) ON DELETE CASCADE"),
    ("ai_metadata", "facebook_post_id", "INTEGER REFERENCES facebook_posts(id) ON DELETE CASCADE"),
    # generated_responses
    ("generated_responses", "twitter_post_id", "INTEGER REFERENCES twitter_posts(id) ON DELETE CASCADE"),
    ("generated_responses", "facebook_post_id", "INTEGER REFERENCES facebook_posts(id) ON DELETE CASCADE"),
    # platform_credentials
    ("platform_credentials", "logged_in", "BOOLEAN DEFAULT FALSE"),
]


async def run():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Create any brand-new tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Created any missing tables")

    # Add missing columns — each in its own transaction so one failure doesn't block the rest
    for table, col, col_type in COLUMNS_TO_ADD:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                ))
                print(f"✅ Added {table}.{col}")
        except Exception as e:
            err = str(e).lower()
            if "already exists" in err or "duplicate" in err:
                print(f"⏭️  {table}.{col} already exists")
            else:
                print(f"⚠️  {table}.{col}: {e}")

    await engine.dispose()
    print("\n🎉 Done! Database is up to date.")


if __name__ == "__main__":
    asyncio.run(run())
