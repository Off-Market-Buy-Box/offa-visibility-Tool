"""Add agent_posted columns to reddit_mentions table"""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def add_columns():
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "ALTER TABLE reddit_mentions ADD COLUMN agent_posted BOOLEAN DEFAULT FALSE"
            ))
            print("✅ Added agent_posted column")
        except Exception as e:
            print(f"⚠️ agent_posted: {e}")

        try:
            await conn.execute(text(
                "ALTER TABLE reddit_mentions ADD COLUMN agent_posted_at TIMESTAMP"
            ))
            print("✅ Added agent_posted_at column")
        except Exception as e:
            print(f"⚠️ agent_posted_at: {e}")

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(add_columns())
