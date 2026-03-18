from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.linkedin import LinkedInPostResponse
from app.services.linkedin_service import LinkedInService
from app.models.linkedin_post import LinkedInPost
from sqlalchemy import select

router = APIRouter()


@router.post("/monitor")
async def monitor_linkedin(
    keywords: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Search LinkedIn for real estate posts via Google/SerpAPI"""
    service = LinkedInService()
    stats = await service.monitor_linkedin(db, keywords)
    return {"message": "LinkedIn monitoring completed", **stats}


@router.get("/posts", response_model=List[LinkedInPostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get stored LinkedIn posts"""
    query = (
        select(LinkedInPost)
        .offset(skip)
        .limit(limit)
        .order_by(LinkedInPost.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/posts/{post_id}", response_model=LinkedInPostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific LinkedIn post"""
    result = await db.execute(
        select(LinkedInPost).where(LinkedInPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a LinkedIn post"""
    result = await db.execute(
        select(LinkedInPost).where(LinkedInPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
    return {"message": "Post deleted"}


@router.post("/posts/{post_id}/fetch-content")
async def fetch_post_content(post_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch the full content of a LinkedIn post by visiting the URL"""
    result = await db.execute(
        select(LinkedInPost).where(LinkedInPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    service = LinkedInService()
    content = await service.fetch_post_content(post.url)

    if content:
        post.content = content
        await db.commit()
        return {"content": content, "success": True}
    else:
        return {"content": None, "success": False, "message": "Could not extract content. The post may require login."}
