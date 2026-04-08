"""Add outreach_targets and outreach_posts tables"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import engine, Base
from app.models.outreach_target import OutreachTarget, OutreachPost


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Outreach tables created")


if __name__ == "__main__":
    asyncio.run(main())
