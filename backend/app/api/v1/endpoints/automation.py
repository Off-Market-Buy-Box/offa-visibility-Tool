from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.automation_log import AutomationLog
from app.services.automation_service import automation

router = APIRouter()


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    status = automation.get_status()
    # Get accurate counts from DB
    for p in ["reddit", "linkedin", "twitter", "facebook"]:
        # Scanned count
        scan_result = await db.execute(
            select(func.coalesce(func.sum(AutomationLog.posts_found), 0))
            .where(AutomationLog.platform == p)
            .where(AutomationLog.action == "scan")
        )
        status["platforms"][p]["total_scanned"] = scan_result.scalar() or 0

        # Commented count
        comment_result = await db.execute(
            select(func.coalesce(func.sum(AutomationLog.posts_commented), 0))
            .where(AutomationLog.platform == p)
            .where(AutomationLog.action == "comment")
        )
        status["platforms"][p]["total_commented"] = comment_result.scalar() or 0

        # Error count
        err_result = await db.execute(
            select(func.coalesce(func.sum(AutomationLog.errors), 0))
            .where(AutomationLog.platform == p)
        )
        status["platforms"][p]["errors"] = err_result.scalar() or 0

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
