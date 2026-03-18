"""
Remove search_volume and difficulty columns from keywords table
Run this after updating the model
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def remove_columns():
    print("=" * 60)
    print("  REMOVING UNUSED COLUMNS FROM KEYWORDS TABLE")
    print("=" * 60)
    
    async with engine.begin() as conn:
        try:
            # Check if columns exist first
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'keywords'
            """))
            columns = [row[0] for row in result]
            
            print(f"\nCurrent columns: {columns}")
            
            # Remove search_volume if it exists
            if 'search_volume' in columns:
                print("\n🗑️  Removing search_volume column...")
                await conn.execute(text("ALTER TABLE keywords DROP COLUMN search_volume"))
                print("✅ search_volume removed")
            else:
                print("\n✓ search_volume already removed")
            
            # Remove difficulty if it exists
            if 'difficulty' in columns:
                print("\n🗑️  Removing difficulty column...")
                await conn.execute(text("ALTER TABLE keywords DROP COLUMN difficulty"))
                print("✅ difficulty removed")
            else:
                print("\n✓ difficulty already removed")
            
            print("\n" + "=" * 60)
            print("✅ DATABASE UPDATED SUCCESSFULLY")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\nNote: If columns don't exist, this is normal.")

if __name__ == "__main__":
    asyncio.run(remove_columns())
