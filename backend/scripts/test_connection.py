"""
Test PostgreSQL connection
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def test_connection():
    print("=" * 60)
    print("  TESTING DATABASE CONNECTION")
    print("=" * 60)
    print(f"\n📍 Trying to connect to: {settings.DATABASE_URL}")
    print("\n🔧 Testing connection...")
    
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            print("\n✅ CONNECTION SUCCESSFUL!")
            print(f"\n📊 PostgreSQL Version:")
            print(f"   {version}")
            
        await engine.dispose()
        
        print("\n🎉 Your database connection is working!")
        print("\n💡 Next step: Create tables")
        print("   Run: python scripts/create_tables.py")
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED!")
        print(f"\n🔴 Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if PostgreSQL is running in pgAdmin")
        print("   2. Verify your password in .env file")
        print("   3. Make sure database 'seo_monitor' exists")
        print("   4. Check if port 5432 is correct")
        print("\n📝 Current connection string:")
        print(f"   {settings.DATABASE_URL}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
