"""
Simple script to create database tables
Run this once to set up your database
"""
import asyncio
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

# Import all models so SQLAlchemy knows about them
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

async def create_tables():
    """Create all database tables"""
    print("=" * 60)
    print("  DATABASE TABLE CREATOR")
    print("=" * 60)
    print("\n🔧 Connecting to database...")
    print(f"📍 Database: seo_monitor")
    
    try:
        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        
        print("\n🏗️  Creating tables...")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("\n✅ SUCCESS! All tables created:")
        print("   ✓ keywords")
        print("   ✓ rankings")
        print("   ✓ competitors")
        print("   ✓ reddit_mentions")
        print("   ✓ smart_tasks")
        print("\n🎉 Your database is ready!")
        print("\n💡 Next step: Start the server")
        print("   Run: uvicorn app.main:app --reload")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n💡 Common fixes:")
        print("   1. Check .env file has correct DATABASE_URL")
        print("   2. Make sure PostgreSQL is running")
        print("   3. Verify database 'seo_monitor' exists in pgAdmin")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_tables())
