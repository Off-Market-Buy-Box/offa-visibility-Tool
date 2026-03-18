from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.models.keyword import Keyword
from app.models.ranking import Ranking
from app.schemas.keyword import KeywordCreate, KeywordUpdate
from app.services.scraper import GoogleScraper

class KeywordService:
    
    @staticmethod
    async def create_keyword(db: AsyncSession, keyword_data: KeywordCreate) -> Keyword:
        keyword = Keyword(**keyword_data.model_dump())
        db.add(keyword)
        await db.commit()
        await db.refresh(keyword)
        return keyword
    
    @staticmethod
    async def get_keywords(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Keyword]:
        result = await db.execute(select(Keyword).offset(skip).limit(limit))
        keywords = result.scalars().all()
        
        # Add best_rank (best position where domain appears in latest search results)
        for keyword in keywords:
            # Get the most recent check time
            latest_check = await db.execute(
                select(Ranking.checked_at)
                .where(Ranking.keyword_id == keyword.id)
                .order_by(Ranking.checked_at.desc())
                .limit(1)
            )
            latest_time = latest_check.scalar_one_or_none()
            
            if latest_time:
                # Get all results from the latest check that contain the domain
                ranking_result = await db.execute(
                    select(Ranking)
                    .where(
                        Ranking.keyword_id == keyword.id,
                        Ranking.checked_at == latest_time
                    )
                    .order_by(Ranking.position)
                )
                all_rankings = ranking_result.scalars().all()
                
                # Find the best (lowest) position where domain appears
                domain_positions = [
                    r.position for r in all_rankings 
                    if r.extra_data and r.extra_data.get("contains_domain", False)
                ]
                keyword.best_rank = min(domain_positions) if domain_positions else None
            else:
                keyword.best_rank = None
        
        return keywords
    
    @staticmethod
    async def get_keyword(db: AsyncSession, keyword_id: int) -> Optional[Keyword]:
        result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_keyword(db: AsyncSession, keyword_id: int, keyword_data: KeywordUpdate) -> Optional[Keyword]:
        keyword = await KeywordService.get_keyword(db, keyword_id)
        if keyword:
            for key, value in keyword_data.model_dump(exclude_unset=True).items():
                setattr(keyword, key, value)
            await db.commit()
            await db.refresh(keyword)
        return keyword
    
    @staticmethod
    async def delete_keyword(db: AsyncSession, keyword_id: int) -> bool:
        keyword = await KeywordService.get_keyword(db, keyword_id)
        if keyword:
            await db.delete(keyword)
            await db.commit()
            return True
        return False
