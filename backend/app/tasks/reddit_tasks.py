from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.reddit_service import RedditService

@celery_app.task
async def monitor_subreddit(subreddit: str, keywords: list):
    """Background task to monitor a subreddit"""
    async with AsyncSessionLocal() as db:
        reddit_service = RedditService()
        
        mentions = await reddit_service.search_subreddit(subreddit, keywords)
        saved_count = await reddit_service.save_mentions(db, mentions)
        
        return {
            "status": "completed",
            "subreddit": subreddit,
            "mentions_found": len(mentions),
            "new_mentions": saved_count
        }

@celery_app.task
async def monitor_all_subreddits():
    """Background task to monitor all configured subreddits"""
    # This would be configured based on user settings
    subreddits = ["SEO", "marketing", "entrepreneur"]
    keywords = ["SEO", "ranking", "keywords"]
    
    results = []
    for subreddit in subreddits:
        result = await monitor_subreddit(subreddit, keywords)
        results.append(result)
    
    return {"status": "completed", "subreddits_monitored": len(results)}
