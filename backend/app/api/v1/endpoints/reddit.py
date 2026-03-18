from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.reddit import RedditMentionResponse
from app.services.reddit_service import RedditService
from app.models.reddit_mention import RedditMention
from sqlalchemy import select

router = APIRouter()

@router.post("/monitor")
async def monitor_subreddit(
    subreddit: str,
    keywords: List[str] = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Monitor a specific subreddit for keyword mentions"""
    reddit_service = RedditService()
    
    mentions = await reddit_service.search_subreddit(subreddit, keywords)
    saved_count = await reddit_service.save_mentions(db, mentions)
    
    return {
        "subreddit": subreddit,
        "mentions_found": len(mentions),
        "new_mentions_saved": saved_count
    }

@router.post("/monitor-real-estate")
async def monitor_real_estate(
    keywords: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Monitor all real estate subreddits for offa.com and related keywords"""
    reddit_service = RedditService()
    
    stats = await reddit_service.monitor_real_estate_mentions(db, keywords)
    
    return {
        "message": "Real estate monitoring completed",
        **stats
    }

@router.get("/mentions", response_model=List[RedditMentionResponse])
async def get_mentions(
    subreddit: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get Reddit mentions"""
    query = select(RedditMention)
    
    if subreddit:
        query = query.where(RedditMention.subreddit == subreddit)
    
    query = query.offset(skip).limit(limit).order_by(RedditMention.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/mentions/{mention_id}", response_model=RedditMentionResponse)
async def get_mention(
    mention_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific Reddit mention"""
    result = await db.execute(select(RedditMention).where(RedditMention.id == mention_id))
    mention = result.scalar_one_or_none()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")
    
    return mention

@router.get("/mentions/{mention_id}/comments")
async def get_mention_comments(
    mention_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get comments for a specific Reddit post"""
    result = await db.execute(select(RedditMention).where(RedditMention.id == mention_id))
    mention = result.scalar_one_or_none()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")
    
    reddit_service = RedditService()
    comments = await reddit_service.get_post_comments(mention.url)
    
    return {"post_id": mention.post_id, "comments": comments}

@router.delete("/mentions/{mention_id}")
async def delete_mention(
    mention_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a Reddit mention"""
    result = await db.execute(select(RedditMention).where(RedditMention.id == mention_id))
    mention = result.scalar_one_or_none()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")
    
    await db.delete(mention)
    await db.commit()
    return {"message": "Mention deleted"}
