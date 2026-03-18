"""
Test real Google search with SerpAPI to see actual results
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.scraper import GoogleScraper

async def test_real_search():
    print("=" * 70)
    print("  TESTING REAL GOOGLE SEARCH WITH SERPAPI")
    print("=" * 70)
    
    scraper = GoogleScraper()
    
    # Test with "off market real estate deals"
    keyword = "off market real estate deals"
    print(f"\n🔍 Searching for: '{keyword}'")
    print(f"🎯 Looking for domain: 'offa.com'\n")
    
    results = await scraper.search(keyword, num_results=10)
    
    print(f"\n📊 RESULTS:")
    print("=" * 70)
    
    offa_positions = []
    
    for result in results:
        position = result['position']
        url = result['url']
        title = result['title'][:60]
        
        # Check if offa.com is in the URL
        is_offa = 'offa' in url.lower()
        
        if is_offa:
            offa_positions.append(position)
            print(f"🎯 #{position}: {url}")
            print(f"    ✅ OFFA.COM FOUND!")
            print(f"    Title: {title}...")
        else:
            print(f"   #{position}: {url}")
            print(f"    Title: {title}...")
        print()
    
    print("=" * 70)
    print(f"\n📈 SUMMARY:")
    print(f"   Total results: {len(results)}")
    print(f"   Offa.com appearances: {len(offa_positions)}")
    
    if offa_positions:
        best_rank = min(offa_positions)
        print(f"   🏆 BEST RANK: #{best_rank}")
        print(f"   All positions: {offa_positions}")
    else:
        print(f"   ❌ Offa.com NOT FOUND in top 10")
    
    print("\n" + "=" * 70)
    
    # Test with another keyword
    print("\n\n")
    keyword2 = "python programming"
    print(f"🔍 Searching for: '{keyword2}'")
    print(f"🎯 Looking for domain: 'python.org'\n")
    
    results2 = await scraper.search(keyword2, num_results=10)
    
    python_positions = []
    for result in results2:
        position = result['position']
        url = result['url']
        is_python = 'python.org' in url.lower()
        
        if is_python:
            python_positions.append(position)
            print(f"🎯 #{position}: {url} ✅")
        else:
            print(f"   #{position}: {url}")
    
    if python_positions:
        print(f"\n🏆 python.org BEST RANK: #{min(python_positions)}")

if __name__ == "__main__":
    asyncio.run(test_real_search())
