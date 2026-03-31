"""
Add missing columns to existing tables:
- ai_metadata: twitter_post_id, facebook_post_id
- generated_responses: facebook_post_id
- Creates facebook_posts and platform_credentials tables if they don't exist
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

# Import all models so Base.metadata knows about them
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
from app.core.database import Base


async def run():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Create any brand-new tables (facebook_posts, platform_credentials)
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Created any missing tables")

        # Add missing columns to ai_metadata
        for col, fk_table in [
            ("twitter_post_id", "twitter_posts"),
            ("facebook_post_id", "facebook_posts"),
        ]:
            try:
                await conn.execute(text(
                    f"ALTER TABLE ai_metadata ADD COLUMN {col} INTEGER REFERENCES {fk_table}(id) ON DELETE CASCADE"
                ))
                print(f"✅ Added ai_metadata.{col}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"⏭️  ai_metadata.{col} already exists")
                else:
                    print(f"⚠️  ai_metadata.{col}: {e}")

        # Add missing columns to generated_responses
        for col, fk_table in [
            ("twitter_post_id", "twitter_posts"),
            ("facebook_post_id", "facebook_posts"),
        ]:
            try:
                await conn.execute(text(
                    f"ALTER TABLE generated_responses ADD COLUMN {col} INTEGER REFERENCES {fk_table}(id) ON DELETE CASCADE"
                ))
                print(f"✅ Added generated_responses.{col}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"⏭️  generated_responses.{col} already exists")
                else:
                    print(f"⚠️  generated_responses.{col}: {e}")

    await engine.dispose()
    print("\n🎉 Done! Database is up to date.")


if __name__ == "__main__":
    asyncio.run(run())
