from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "seo_monitor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.ranking_tasks", "app.tasks.reddit_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-rankings-daily": {
            "task": "app.tasks.ranking_tasks.check_all_rankings",
            "schedule": 86400.0,  # 24 hours
        },
        "monitor-reddit-hourly": {
            "task": "app.tasks.reddit_tasks.monitor_all_subreddits",
            "schedule": 3600.0,  # 1 hour
        },
    }
)
