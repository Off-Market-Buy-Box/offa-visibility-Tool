"""
Comprehensive verification of SerpAPI setup
"""
import sys
sys.path.insert(0, '.')

from app.core.config import settings
from app.services.scraper import GoogleScraper

print("=" * 60)
print("  SERPAPI SETUP VERIFICATION")
print("=" * 60)

# Check 1: Settings
print("\n1️⃣  Checking Settings Object:")
print(f"   SERP_API_KEY: {settings.SERP_API_KEY[:30]}..." if settings.SERP_API_KEY else "   ❌ SERP_API_KEY not found in settings")

# Check 2: Scraper Initialization
print("\n2️⃣  Checking Scraper Initialization:")
scraper = GoogleScraper()
print(f"   use_serp_api: {scraper.use_serp_api}")
print(f"   use_mock_data: {scraper.use_mock_data}")

# Check 3: Summary
print("\n" + "=" * 60)
if scraper.use_serp_api:
    print("✅ SUCCESS! SerpAPI is configured correctly")
    print("   Your app will use REAL Google search results")
    print("\n   Next step: Restart your backend if it's running")
else:
    print("❌ PROBLEM! SerpAPI is NOT configured")
    print("   Your app will use MOCK data")
    print("\n   Fix: Check that SERP_API_KEY is in backend/.env")
print("=" * 60)
