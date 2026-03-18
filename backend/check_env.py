"""
Quick check to verify environment variables are loaded
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("  ENVIRONMENT VARIABLES CHECK")
print("=" * 60)

serp_key = os.getenv("SERP_API_KEY", "")
db_url = os.getenv("DATABASE_URL", "")

print(f"\n✅ DATABASE_URL: {db_url[:50]}..." if db_url else "\n❌ DATABASE_URL not found")
print(f"✅ SERP_API_KEY: {serp_key[:30]}..." if serp_key else "❌ SERP_API_KEY not found")

if serp_key:
    print(f"\n🎉 SerpAPI key is loaded correctly!")
    print(f"   Length: {len(serp_key)} characters")
    print(f"   First 20 chars: {serp_key[:20]}...")
else:
    print(f"\n⚠️  SERP_API_KEY is NOT set!")
    print(f"   Make sure it's in backend/.env file")
    print(f"   Current working directory: {os.getcwd()}")
