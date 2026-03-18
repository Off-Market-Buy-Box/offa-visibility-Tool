from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.scraper import GoogleScraper
from app.models.keyword import Keyword
from app.models.ranking import Ranking
from sqlalchemy import select

@celery_app.task
async def check_keyword_ranking(keyword_id: int):
    """Background task to check ranking for a specific keyword"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
        keyword = result.scalar_one_or_none()
        
        if not keyword or not keyword.is_active:
            return {"status": "skipped", "reason": "keyword not found or inactive"}
        
        scraper = GoogleScraper()
        results = await scraper.search(keyword.keyword)
        
        saved_count = 0
        for result in results:
            if keyword.domain in result["url"]:
                ranking = Ranking(
                    keyword_id=keyword_id,
                    position=result["position"],
                    url=result["url"],
                    title=result["title"],
                    snippet=result["snippet"]
                )
                db.add(ranking)
                saved_count += 1
        
        await db.commit()
        return {"status": "completed", "rankings_saved": saved_count}

@celery_app.task
async def check_all_rankings():
    """Background task to check all active keywords"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Keyword).where(Keyword.is_active == True))
        keywords = result.scalars().all()
        
        for keyword in keywords:
            await check_keyword_ranking(keyword.id)
        
        return {"status": "completed", "keywords_checked": len(keywords)}
