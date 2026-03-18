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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

