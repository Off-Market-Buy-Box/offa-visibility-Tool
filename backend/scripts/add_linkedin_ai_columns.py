"""Add linkedin_post_id columns to ai_metadata and generated_responses tables"""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def add_columns():
    async with engine.begin() as conn:
        # Add linkedin_post_id to ai_metadata
        try:
            await conn.execute(text(
                "ALTER TABLE ai_metadata ADD COLUMN linkedin_post_id INTEGER REFERENCES linkedin_posts(id) ON DELETE CASCADE"
            ))
            print("✅ Added linkedin_post_id to ai_metadata")
        except Exception as e:
            print(f"⚠️ ai_metadata column: {e}")

        # Make reddit_mention_id nullable in ai_metadata
        try:
            await conn.execute(text(
                "ALTER TABLE ai_metadata ALTER COLUMN reddit_mention_id DROP NOT NULL"
            ))
            print("✅ Made reddit_mention_id nullable in ai_metadata")
        except Exception as e:
            print(f"⚠️ ai_metadata nullable: {e}")

        # Drop unique constraint on reddit_mention_id if exists, add new one
        try:
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_metadata_linkedin_post_id ON ai_metadata(linkedin_post_id)"
            ))
            print("✅ Added unique index on linkedin_post_id in ai_metadata")
        except Exception as e:
            print(f"⚠️ ai_metadata index: {e}")

        # Add linkedin_post_id to generated_responses
        try:
            await conn.execute(text(
                "ALTER TABLE generated_responses ADD COLUMN linkedin_post_id INTEGER REFERENCES linkedin_posts(id) ON DELETE CASCADE"
            ))
            print("✅ Added linkedin_post_id to generated_responses")
        except Exception as e:
            print(f"⚠️ generated_responses column: {e}")

        # Make reddit_mention_id nullable in generated_responses
        try:
            await conn.execute(text(
                "ALTER TABLE generated_responses ALTER COLUMN reddit_mention_id DROP NOT NULL"
            ))
            print("✅ Made reddit_mention_id nullable in generated_responses")
        except Exception as e:
            print(f"⚠️ generated_responses nullable: {e}")

        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_generated_responses_linkedin_post_id ON generated_responses(linkedin_post_id)"
            ))
            print("✅ Added index on linkedin_post_id in generated_responses")
        except Exception as e:
            print(f"⚠️ generated_responses index: {e}")

    print("\n✅ Done! LinkedIn AI columns added.")


if __name__ == "__main__":
    asyncio.run(add_columns())
