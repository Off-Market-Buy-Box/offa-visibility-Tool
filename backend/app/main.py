from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router

# Import all models so Base.metadata knows about them
from app.models.keyword import Keyword  # noqa
from app.models.ranking import Ranking  # noqa
from app.models.competitor import Competitor  # noqa
from app.models.reddit_mention import RedditMention  # noqa
from app.models.smart_task import SmartTask  # noqa
from app.models.ai_metadata import AIMetadata  # noqa
from app.models.generated_response import GeneratedResponse  # noqa
from app.models.linkedin_post import LinkedInPost  # noqa
from app.models.twitter_post import TwitterPost  # noqa
from app.models.facebook_post import FacebookPost  # noqa
from app.models.platform_credential import PlatformCredential  # noqa
from app.models.automation_log import AutomationLog  # noqa
from app.models.outreach_target import OutreachTarget, OutreachPost  # noqa

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def cleanup_old_posts():
    """Remove old uncommented posts (>30 days) on every server start"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import delete, and_
        from app.core.database import AsyncSessionLocal
        from app.models.reddit_mention import RedditMention

        cutoff = datetime.utcnow() - timedelta(days=30)
        async with AsyncSessionLocal() as db:
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
            if deleted > 0:
                print(f"🧹 Startup cleanup: removed {deleted} old uncommented Reddit posts")
    except Exception as e:
        print(f"⚠️ Startup cleanup error (non-fatal): {e}")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

