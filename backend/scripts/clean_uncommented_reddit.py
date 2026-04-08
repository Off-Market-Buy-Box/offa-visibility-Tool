#!/usr/bin/env python3
"""
Clean up Reddit mentions that were never commented on.
Keeps only posts where agent_posted = True.
Cascade deletes will auto-remove related ai_metadata and generated_responses.

Usage:
  cd backend
  python scripts/clean_uncommented_reddit.py          # dry run (default)
  python scripts/clean_uncommented_reddit.py --apply   # actually delete
"""
import argparse
import asyncio
import os
import sys

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://offa:offa_secret@localhost:5432/seo_monitor",
)

# asyncpg needs raw postgres:// URL
raw_url = DB_URL.replace("postgresql+asyncpg://", "postgresql://")


async def run(apply: bool):
    import asyncpg

    conn = await asyncpg.connect(raw_url)
    try:
        total = await conn.fetchval("SELECT COUNT(*) FROM reddit_mentions")
        commented = await conn.fetchval("SELECT COUNT(*) FROM reddit_mentions WHERE agent_posted = TRUE")
        to_delete = total - commented

        print(f"📊 Reddit mentions total:     {total}")
        print(f"✅ Commented (agent_posted):   {commented}")
        print(f"🗑  Uncommented (to remove):   {to_delete}")

        if to_delete == 0:
            print("\nNothing to clean up.")
            return

        if not apply:
            print("\n⚠️  Dry run — no changes made. Run with --apply to delete.")
            return

        result = await conn.execute(
            "DELETE FROM reddit_mentions WHERE agent_posted = FALSE OR agent_posted IS NULL"
        )
        deleted = int(result.split()[-1])
        print(f"\n✅ Deleted {deleted} uncommented Reddit mentions (cascade cleaned ai_metadata & generated_responses).")

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description="Remove uncommented Reddit mentions")
    parser.add_argument("--apply", action="store_true", help="Actually delete (default is dry run)")
    args = parser.parse_args()
    asyncio.run(run(args.apply))


if __name__ == "__main__":
    main()
