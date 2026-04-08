from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete
from typing import Optional
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.automation_log import AutomationLog
from app.services.automation_service import automation

router = APIRouter()


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    from app.models.reddit_mention import RedditMention
    from app.models.linkedin_post import LinkedInPost
    from app.models.twitter_post import TwitterPost
    from app.models.facebook_post import FacebookPost

    status = automation.get_status()

    model_map = {
        "reddit": RedditMention,
        "linkedin": LinkedInPost,
        "twitter": TwitterPost,
        "facebook": FacebookPost,
    }

    for p, Model in model_map.items():
        # Scanned = total rows in the table
        total = await db.execute(select(func.count(Model.id)))
        status["platforms"][p]["total_scanned"] = total.scalar() or 0

        # Commented = rows where agent_posted is True
        commented = await db.execute(
            select(func.count(Model.id)).where(Model.agent_posted == True)
        )
        status["platforms"][p]["total_commented"] = commented.scalar() or 0

        # Errors from automation logs
        err_result = await db.execute(
            select(func.coalesce(func.sum(AutomationLog.errors), 0))
            .where(AutomationLog.platform == p)
        )
        status["platforms"][p]["errors"] = err_result.scalar() or 0

        # Last scan time from the most recent scan log
        last_scan = await db.execute(
            select(AutomationLog.created_at)
            .where(AutomationLog.platform == p)
            .where(AutomationLog.action == "scan")
            .order_by(desc(AutomationLog.created_at))
            .limit(1)
        )
        row = last_scan.scalar()
        if row:
            status["platforms"][p]["last_scan"] = row.isoformat()

        # Last comment time from the actual data
        last_comment = await db.execute(
            select(Model.agent_posted_at)
            .where(Model.agent_posted == True)
            .order_by(desc(Model.agent_posted_at))
            .limit(1)
        )
        row = last_comment.scalar()
        if row:
            status["platforms"][p]["last_comment"] = row.isoformat()

    return status


@router.post("/start")
async def start_automation():
    await automation.start()
    return {"message": "Automation started", "running": True}


@router.post("/stop")
async def stop_automation():
    await automation.stop()
    return {"message": "Automation stopped", "running": False}


class SettingsUpdate(BaseModel):
    delay_between_platforms: Optional[int] = None
    delay_between_cycles: Optional[int] = None
    max_posts_per_run: Optional[int] = None
    platforms: Optional[dict] = None


@router.put("/settings")
async def update_settings(req: SettingsUpdate):
    automation.update_settings(req.dict(exclude_none=True))
    return automation.get_status()


@router.get("/logs")
async def get_logs(
    platform: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(AutomationLog).order_by(desc(AutomationLog.created_at)).limit(limit)
    if platform:
        query = query.where(AutomationLog.platform == platform)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "platform": l.platform,
            "action": l.action,
            "posts_found": l.posts_found,
            "posts_commented": l.posts_commented,
            "errors": l.errors,
            "details": l.details,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate stats per platform"""
    result = await db.execute(
        select(
            AutomationLog.platform,
            func.sum(AutomationLog.posts_found).label("total_found"),
            func.sum(AutomationLog.posts_commented).label("total_commented"),
            func.sum(AutomationLog.errors).label("total_errors"),
            func.count(AutomationLog.id).label("total_runs"),
        )
        .group_by(AutomationLog.platform)
    )
    rows = result.all()
    return {
        row.platform: {
            "total_found": row.total_found or 0,
            "total_commented": row.total_commented or 0,
            "total_errors": row.total_errors or 0,
            "total_runs": row.total_runs or 0,
        }
        for row in rows
    }


@router.get("/commented-posts")
async def get_commented_posts(
    platform: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get posts that have been commented on by the agent, across all platforms"""
    from app.models.reddit_mention import RedditMention
    from app.models.linkedin_post import LinkedInPost
    from app.models.twitter_post import TwitterPost
    from app.models.facebook_post import FacebookPost

    results = []

    platforms_to_check = [platform] if platform else ["reddit", "linkedin", "twitter", "facebook"]

    for p in platforms_to_check:
        if p == "reddit":
            q = select(RedditMention).where(RedditMention.agent_posted == True).order_by(desc(RedditMention.agent_posted_at)).limit(limit)
            rows = (await db.execute(q)).scalars().all()
            for r in rows:
                results.append({"platform": "reddit", "id": r.id, "title": r.title, "url": r.url, "author": r.author, "posted_at": r.agent_posted_at.isoformat() if r.agent_posted_at else None})
        elif p == "linkedin":
            q = select(LinkedInPost).where(LinkedInPost.agent_posted == True).order_by(desc(LinkedInPost.agent_posted_at)).limit(limit)
            rows = (await db.execute(q)).scalars().all()
            for r in rows:
                results.append({"platform": "linkedin", "id": r.id, "title": r.title, "url": r.url, "author": r.author, "posted_at": r.agent_posted_at.isoformat() if r.agent_posted_at else None})
        elif p == "twitter":
            q = select(TwitterPost).where(TwitterPost.agent_posted == True).order_by(desc(TwitterPost.agent_posted_at)).limit(limit)
            rows = (await db.execute(q)).scalars().all()
            for r in rows:
                results.append({"platform": "twitter", "id": r.id, "title": r.title, "url": r.url, "author": r.author, "posted_at": r.agent_posted_at.isoformat() if r.agent_posted_at else None})
        elif p == "facebook":
            q = select(FacebookPost).where(FacebookPost.agent_posted == True).order_by(desc(FacebookPost.agent_posted_at)).limit(limit)
            rows = (await db.execute(q)).scalars().all()
            for r in rows:
                results.append({"platform": "facebook", "id": r.id, "title": r.title, "url": r.url, "author": r.author, "posted_at": r.agent_posted_at.isoformat() if r.agent_posted_at else None})

    results.sort(key=lambda x: x.get("posted_at") or "", reverse=True)
    return results[:limit]


@router.post("/clear-all")
async def clear_all_data(db: AsyncSession = Depends(get_db)):
    """Delete all scanned posts, comments, logs, AI metadata — everything"""
    from app.models.reddit_mention import RedditMention
    from app.models.linkedin_post import LinkedInPost
    from app.models.twitter_post import TwitterPost
    from app.models.facebook_post import FacebookPost
    from app.models.generated_response import GeneratedResponse
    from app.models.ai_metadata import AIMetadata

    for model in [GeneratedResponse, AIMetadata, AutomationLog, RedditMention, LinkedInPost, TwitterPost, FacebookPost]:
        await db.execute(delete(model))

    await db.commit()

    # Reset in-memory counters
    for p in ["reddit", "linkedin", "twitter", "facebook"]:
        automation._status["platforms"][p].update({
            "last_scan": None,
            "last_comment": None,
            "total_commented": 0,
            "total_scanned": 0,
            "errors": 0,
        })
    automation._status["cycle_count"] = 0
    automation._status["last_cycle_at"] = None

    return {"message": "All data cleared"}
