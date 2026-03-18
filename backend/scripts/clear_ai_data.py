"""Clear all AI metadata and generated responses from the database."""
import asyncio
import sys
sys.path.insert(0, ".")

from sqlalchemy import text
from app.core.database import engine

async def clear():
    async with engine.begin() as conn:
        r1 = await conn.execute(text("DELETE FROM generated_responses"))
        r2 = await conn.execute(text("DELETE FROM ai_metadata"))
        print(f"Deleted {r1.rowcount} generated responses")
        print(f"Deleted {r2.rowcount} AI metadata entries")
        print("Done - clean slate!")

asyncio.run(clear())
