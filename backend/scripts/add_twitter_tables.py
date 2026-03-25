"""Create twitter_posts table and add twitter_post_id to ai_metadata and generated_responses"""

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def create_tables():
    async with engine.begin() as conn:
        # Create twitter_posts table
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS twitter_posts (
                    id SERIAL PRIMARY KEY,
                    tweet_id VARCHAR UNIQUE NOT NULL,
                    title VARCHAR NOT NULL,
                    snippet TEXT,
                    content TEXT,
                    url VARCHAR NOT NULL,
                    author VARCHAR,
                    source VARCHAR DEFAULT 'twitter.com',
                    keywords_matched VARCHAR,
                    is_relevant BOOLEAN DEFAULT TRUE,
                    agent_posted BOOLEAN DEFAULT FALSE,
                    agent_posted_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    posted_at TIMESTAMP
                )
            """))
            print("✅ Created twitter_posts table")
        except Exception as e:
            print(f"⚠️ twitter_posts table: {e}")

        # Create index on tweet_id
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_twitter_posts_tweet_id ON twitter_posts(tweet_id)"
            ))
            print("✅ Created index on tweet_id")
        except Exception as e:
            print(f"⚠️ tweet_id index: {e}")

        # Add twitter_post_id to ai_metadata
        try:
            await conn.execute(text(
                "ALTER TABLE ai_metadata ADD COLUMN twitter_post_id INTEGER REFERENCES twitter_posts(id) ON DELETE CASCADE"
            ))
            print("✅ Added twitter_post_id to ai_metadata")
        except Exception as e:
            print(f"⚠️ ai_metadata column: {e}")

        try:
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_metadata_twitter_post_id ON ai_metadata(twitter_post_id)"
            ))
            print("✅ Added unique index on twitter_post_id in ai_metadata")
        except Exception as e:
            print(f"⚠️ ai_metadata index: {e}")

        # Add twitter_post_id to generated_responses
        try:
            await conn.execute(text(
                "ALTER TABLE generated_responses ADD COLUMN twitter_post_id INTEGER REFERENCES twitter_posts(id) ON DELETE CASCADE"
            ))
            print("✅ Added twitter_post_id to generated_responses")
        except Exception as e:
            print(f"⚠️ generated_responses column: {e}")

        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_generated_responses_twitter_post_id ON generated_responses(twitter_post_id)"
            ))
            print("✅ Added index on twitter_post_id in generated_responses")
        except Exception as e:
            print(f"⚠️ generated_responses index: {e}")

    print("\n✅ Done! Twitter tables and columns added.")


if __name__ == "__main__":
    asyncio.run(create_tables())
