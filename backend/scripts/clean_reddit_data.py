"""
Clean all old Reddit data from the database.
Removes: reddit_mentions, related ai_metadata, and generated_responses.

Run from backend folder:
  python scripts/clean_reddit_data.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def clean():
    async with AsyncSessionLocal() as db:
        # Delete generated responses linked to reddit mentions
        r1 = await db.execute(text("DELETE FROM generated_responses WHERE reddit_mention_id IS NOT NULL"))
        print(f"Deleted {r1.rowcount} generated responses (reddit)")

        # Delete ai metadata linked to reddit mentions
        r2 = await db.execute(text("DELETE FROM ai_metadata WHERE reddit_mention_id IS NOT NULL"))
        print(f"Deleted {r2.rowcount} AI metadata (reddit)")

        # Delete all reddit mentions
        r3 = await db.execute(text("DELETE FROM reddit_mentions"))
        print(f"Deleted {r3.rowcount} reddit mentions")

        await db.commit()
        print("Done! Reddit data cleaned.")


if __name__ == "__main__":
    asyncio.run(clean())
