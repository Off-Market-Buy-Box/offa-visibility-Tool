"""
Test the Google scraper directly
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, '.')

from app.services.scraper import GoogleScraper

async def test_scraper():
    print("=" * 60)
    print("  TESTING GOOGLE SCRAPER")
    print("=" * 60)
    
    # Show loaded environment variables
    api_key = os.getenv("GOOGLE_API_KEY", "")
    cse_id = os.getenv("GOOGLE_CSE_ID", "")
    print(f"\n🔑 API Key: {api_key[:20]}..." if api_key else "\n❌ No API Key found")
    print(f"🔑 CSE ID: {cse_id}" if cse_id else "❌ No CSE ID found")
    
    scraper = GoogleScraper()
    
    # Test with a simple keyword
    keyword = "python"
    print(f"\n🔍 Testing search for: {keyword}\n")
    
    results = await scraper.search(keyword)
    
    print(f"\n📊 Results Summary:")
    print(f"   Total results found: {len(results)}")
    
    if results:
        print(f"\n✅ Top 5 Results:")
        for result in results[:5]:
            print(f"   #{result['position']}: {result['url']}")
            print(f"      Title: {result['title'][:60]}...")
    else:
        print("\n❌ No results found")

if __name__ == "__main__":
    asyncio.run(test_scraper())
