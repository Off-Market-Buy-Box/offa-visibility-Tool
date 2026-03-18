from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas.competitor import CompetitorCreate, CompetitorUpdate, CompetitorResponse
from app.models.competitor import Competitor
from sqlalchemy import select

router = APIRouter()

@router.post("/", response_model=CompetitorResponse)
async def create_competitor(
    competitor: CompetitorCreate,
    db: AsyncSession = Depends(get_db)
):
    db_competitor = Competitor(**competitor.model_dump())
    db.add(db_competitor)
    await db.commit()
    await db.refresh(db_competitor)
    return db_competitor

@router.get("/", response_model=List[CompetitorResponse])
async def get_competitors(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Competitor).offset(skip).limit(limit))
    return result.scalars().all()
