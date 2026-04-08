from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.outreach_target import OutreachTarget, OutreachPost
from app.services.outreach_service import outreach_automation

router = APIRouter()

# Only PUBLIC subreddits where anyone can post (no private/restricted)
DEFAULT_SUBREDDITS = [
    # --- Real Estate Investing (open, large) ---
    {"name": "r/realestateinvesting", "url": "https://www.reddit.com/r/realestateinvesting/"},
    {"name": "r/RealEstate", "url": "https://www.reddit.com/r/RealEstate/"},
    {"name": "r/CommercialRealEstate", "url": "https://www.reddit.com/r/CommercialRealEstate/"},
    {"name": "r/rentalproperty", "url": "https://www.reddit.com/r/rentalproperty/"},
    {"name": "r/landlord", "url": "https://www.reddit.com/r/landlord/"},
    # --- Wholesaling (open) ---
    {"name": "r/WholesaleRealestate", "url": "https://www.reddit.com/r/WholesaleRealestate/"},
    {"name": "r/wholesaling", "url": "https://www.reddit.com/r/wholesaling/"},
    # --- Flipping (open) ---
    {"name": "r/Flipping", "url": "https://www.reddit.com/r/Flipping/"},
    {"name": "r/fixandflip", "url": "https://www.reddit.com/r/fixandflip/"},
    # --- Buyers & Market (open) ---
    {"name": "r/FirstTimeHomeBuyer", "url": "https://www.reddit.com/r/FirstTimeHomeBuyer/"},
    {"name": "r/homeowners", "url": "https://www.reddit.com/r/homeowners/"},
    {"name": "r/REBubble", "url": "https://www.reddit.com/r/REBubble/"},
    # --- Entrepreneurship (open, large) ---
    {"name": "r/Entrepreneur", "url": "https://www.reddit.com/r/Entrepreneur/"},
    {"name": "r/smallbusiness", "url": "https://www.reddit.com/r/smallbusiness/"},
    {"name": "r/passive_income", "url": "https://www.reddit.com/r/passive_income/"},
    # --- Financial Independence ---
    {"name": "r/financialindependence", "url": "https://www.reddit.com/r/financialindependence/"},
    {"name": "r/Fire", "url": "https://www.reddit.com/r/Fire/"},
    {"name": "r/personalfinance", "url": "https://www.reddit.com/r/personalfinance/"},
]


class TargetCreate(BaseModel):
    name: str
    url: str


class TargetUpdate(BaseModel):
    enabled: Optional[bool] = None
    name: Optional[str] = None


class SettingsUpdate(BaseModel):
    interval_hours: Optional[int] = None


_defaults_seeded = False


@router.get("/status")
async def get_outreach_status(db: AsyncSession = Depends(get_db)):
    global _defaults_seeded
    # Auto-seed default subreddits on first call if table is empty
    if not _defaults_seeded:
        _defaults_seeded = True
        existing = await db.execute(select(OutreachTarget).limit(1))
        if not existing.scalar_one_or_none():
            for sub in DEFAULT_SUBREDDITS:
                db.add(OutreachTarget(platform="reddit", name=sub["name"], url=sub["url"]))
            await db.commit()

    status = outreach_automation.get_status()
    result = await db.execute(select(OutreachTarget).where(OutreachTarget.enabled == True))
    status["enabled_targets"] = len(result.scalars().all())
    return status


@router.post("/start")
async def start_outreach():
    await outreach_automation.start()
    return {"message": "Outreach started", "running": True}


@router.post("/stop")
async def stop_outreach():
    await outreach_automation.stop()
    return {"message": "Outreach stopped", "running": False}


@router.put("/settings")
async def update_outreach_settings(req: SettingsUpdate):
    outreach_automation.update_settings(req.dict(exclude_none=True))
    return outreach_automation.get_status()


@router.get("/targets")
async def list_targets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OutreachTarget).order_by(OutreachTarget.created_at.desc())
    )
    targets = result.scalars().all()
    return [
        {
            "id": t.id, "platform": t.platform, "name": t.name, "url": t.url,
            "enabled": t.enabled,
            "last_posted_at": t.last_posted_at.isoformat() if t.last_posted_at else None,
            "total_posts": t.total_posts,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in targets
    ]


@router.get("/defaults")
async def get_defaults():
    """Return the list of popular subreddits for quick-add"""
    return DEFAULT_SUBREDDITS


@router.post("/targets")
async def add_target(req: TargetCreate, db: AsyncSession = Depends(get_db)):
    target = OutreachTarget(platform="reddit", name=req.name, url=req.url)
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return {"id": target.id, "name": target.name, "url": target.url}


@router.post("/targets/add-defaults")
async def add_default_targets(db: AsyncSession = Depends(get_db)):
    """Add all default subreddits that aren't already added"""
    added = 0
    for sub in DEFAULT_SUBREDDITS:
        existing = await db.execute(
            select(OutreachTarget).where(OutreachTarget.url == sub["url"])
        )
        if not existing.scalar_one_or_none():
            db.add(OutreachTarget(platform="reddit", name=sub["name"], url=sub["url"]))
            added += 1
    await db.commit()
    return {"added": added}


@router.put("/targets/{target_id}")
async def update_target(target_id: int, req: TargetUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OutreachTarget).where(OutreachTarget.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "Target not found")
    if req.enabled is not None:
        target.enabled = req.enabled
    if req.name is not None:
        target.name = req.name
    await db.commit()
    return {"ok": True}


@router.delete("/targets/{target_id}")
async def delete_target(target_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(OutreachPost).where(OutreachPost.target_id == target_id))
    await db.execute(delete(OutreachTarget).where(OutreachTarget.id == target_id))
    await db.commit()
    return {"ok": True}


@router.get("/posts")
async def list_posts(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OutreachPost).order_by(desc(OutreachPost.created_at)).limit(limit)
    )
    posts = result.scalars().all()
    return [
        {
            "id": p.id, "target_id": p.target_id, "platform": p.platform,
            "title": p.title, "content": p.content, "status": p.status,
            "error": p.error,
            "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in posts
    ]


@router.post("/generate-preview")
async def generate_preview(db: AsyncSession = Depends(get_db)):
    """Generate a preview Reddit post"""
    from app.services.ai_service import AIService
    ai = AIService()
    result = await ai.generate_reddit_outreach_post()
    return result


@router.post("/run")
async def run_outreach_now():
    """Trigger one outreach cycle manually (posts to all enabled subreddits not posted today)"""
    if outreach_automation._running:
        return {"message": "Already running in background"}
    try:
        await outreach_automation._run_cycle(raise_errors=True)
        return {"message": "Manual outreach cycle complete"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/test-browser")
async def test_browser():
    """Test if Playwright/Chromium can launch — uses same subprocess as commenting"""
    import json as _json
    try:
        from app.services.reddit_poster_browser import RedditPosterBrowser
        poster = RedditPosterBrowser()
        result = await poster.test_browser()
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))
