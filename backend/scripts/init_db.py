import asyncio
from app.core.database import engine, Base
from app.models import keyword, ranking, competitor, reddit_mention, smart_task

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
