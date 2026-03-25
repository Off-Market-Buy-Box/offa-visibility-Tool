from fastapi import APIRouter
from app.api.v1.endpoints import keywords, rankings, competitors, reddit, smart_tasks, ai, linkedin, twitter

api_router = APIRouter()

api_router.include_router(keywords.router, prefix="/keywords", tags=["keywords"])
api_router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
api_router.include_router(competitors.router, prefix="/competitors", tags=["competitors"])
api_router.include_router(reddit.router, prefix="/reddit", tags=["reddit"])
api_router.include_router(smart_tasks.router, prefix="/smart-tasks", tags=["smart-tasks"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(linkedin.router, prefix="/linkedin", tags=["linkedin"])
api_router.include_router(twitter.router, prefix="/twitter", tags=["twitter"])
