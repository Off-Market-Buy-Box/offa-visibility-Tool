"""
Test SerpAPI integration directly
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, '.')

from app.services.scraper import GoogleScraper

async def test_serpapi():
    print("=" * 60)
    print("  TESTING SERPAPI INTEGRATION")
    print("=" * 60)
    
    api_key = os.getenv("SERP_API_KEY", "")
    print(f"\n🔑 SerpAPI Key: {api_key[:20]}..." if api_key else "\n❌ No SerpAPI Key found")
    
    scraper = GoogleScraper()
    
    # Test with real estate keyword
    keyword = "off market real estate deals"
    print(f"\n🔍 Testing search for: {keyword}\n")
    
    results = await scraper.search(keyword, num_results=10)
    
    print(f"\n📊 Results Summary:")
    print(f"   Total results found: {len(results)}")
    
    if results:
        print(f"\n✅ Top 10 Results:")
        for result in results:
            print(f"   #{result['position']}: {result['url']}")
            print(f"      Title: {result['title'][:70]}...")
            
            # Check if offa.com appears in results
            if 'offa' in result['url'].lower():
                print(f"      🎯 FOUND OFFA.COM at position {result['position']}!")
    else:
        print("\n❌ No results found")
    
    # Test with another keyword
    print("\n" + "=" * 60)
    keyword2 = "python programming"
    print(f"\n🔍 Testing search for: {keyword2}\n")
    
    results2 = await scraper.search(keyword2, num_results=5)
    
    print(f"\n📊 Results Summary:")
    print(f"   Total results found: {len(results2)}")
    
    if results2:
        print(f"\n✅ Top 5 Results:")
        for result in results2[:5]:
            print(f"   #{result['position']}: {result['url']}")

if __name__ == "__main__":
    asyncio.run(test_serpapi())
