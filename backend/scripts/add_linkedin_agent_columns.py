"""Add agent_posted and agent_posted_at columns to linkedin_posts table"""

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def add_columns():
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "ALTER TABLE linkedin_posts ADD COLUMN agent_posted BOOLEAN DEFAULT FALSE"
            ))
            print("✅ Added agent_posted to linkedin_posts")
        except Exception as e:
            print(f"⚠️ agent_posted column: {e}")

        try:
            await conn.execute(text(
                "ALTER TABLE linkedin_posts ADD COLUMN agent_posted_at TIMESTAMP"
            ))
            print("✅ Added agent_posted_at to linkedin_posts")
        except Exception as e:
            print(f"⚠️ agent_posted_at column: {e}")

    print("\n✅ Done! LinkedIn agent columns added.")


if __name__ == "__main__":
    asyncio.run(add_columns())
