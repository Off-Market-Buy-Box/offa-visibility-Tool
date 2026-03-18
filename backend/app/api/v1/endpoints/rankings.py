from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas.ranking import RankingCreate, RankingResponse
from app.services.scraper import GoogleScraper
from app.models.ranking import Ranking
from app.models.keyword import Keyword
from sqlalchemy import select

router = APIRouter()

@router.post("/check/{keyword_id}")
async def check_ranking(
    keyword_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    scraper = GoogleScraper()
    results = await scraper.search(keyword.keyword)
    
    # Save ALL results, marking which ones contain your domain
    domain_found_count = 0
    for result in results:
        # Check if this result contains your domain
        contains_domain = keyword.domain.lower() in result["url"].lower()
        if contains_domain:
            domain_found_count += 1
        
        ranking = Ranking(
            keyword_id=keyword_id,
            position=result["position"],
            url=result["url"],
            title=result["title"],
            snippet=result["snippet"],
            extra_data={"contains_domain": contains_domain}  # Mark if it's your domain
        )
        db.add(ranking)
    
    await db.commit()
    return {
        "message": "Ranking check completed", 
        "total_results": len(results),
        "domain_found_count": domain_found_count
    }

@router.get("/{keyword_id}/results", response_model=List[RankingResponse])
async def get_keyword_results(
    keyword_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the latest search results for a keyword"""
    # Get the most recent check time for this keyword
    latest_check = await db.execute(
        select(Ranking.checked_at)
        .where(Ranking.keyword_id == keyword_id)
        .order_by(Ranking.checked_at.desc())
        .limit(1)
    )
    latest_time = latest_check.scalar_one_or_none()
    
    if not latest_time:
        return []
    
    # Get all results from that check
    results = await db.execute(
        select(Ranking)
        .where(Ranking.keyword_id == keyword_id, Ranking.checked_at == latest_time)
        .order_by(Ranking.position)
    )
    return results.scalars().all()
