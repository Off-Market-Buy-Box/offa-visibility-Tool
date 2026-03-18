from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas.keyword import KeywordCreate, KeywordUpdate, KeywordResponse
from app.services.keyword_service import KeywordService

router = APIRouter()

@router.post("/", response_model=KeywordResponse)
async def create_keyword(
    keyword: KeywordCreate,
    db: AsyncSession = Depends(get_db)
):
    return await KeywordService.create_keyword(db, keyword)

@router.get("/", response_model=List[KeywordResponse])
async def get_keywords(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await KeywordService.get_keywords(db, skip, limit)

@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db)
):
    keyword = await KeywordService.get_keyword(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword

@router.delete("/{keyword_id}")
async def delete_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db)
):
    keyword = await KeywordService.get_keyword(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    await KeywordService.delete_keyword(db, keyword_id)
    return {"message": "Keyword deleted successfully"}
