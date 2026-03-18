from typing import List, Dict
import httpx
from app.core.config import settings

class GoogleScraper:
    """Scraper for Google search results using SerpAPI or mock data"""
    
    def __init__(self):
        # SerpAPI is the recommended solution for production
        self.serp_api_key = settings.SERP_API_KEY
        self.use_serp_api = bool(self.serp_api_key)
        self.use_mock_data = not self.use_serp_api  # Use mock if no API key
        
        # Debug logging
        if self.use_serp_api:
            print(f"✅ SerpAPI initialized with key: {self.serp_api_key[:20]}...")
        else:
            print("⚠️  No SERP_API_KEY found - using mock data")
    
    async def search(self, keyword: str, num_results: int = 10) -> List[Dict]:
        """Search Google using SerpAPI or fallback to mock data"""
        
        # Try SerpAPI first if configured
        if self.use_serp_api:
            try:
                return await self._search_with_serpapi(keyword, num_results)
            except Exception as e:
                print(f"❌ SerpAPI search failed: {e}")
                print("⚠️  Falling back to mock data")
                return self._get_mock_results(keyword)
        
        # Use mock data if no API key configured
        return self._get_mock_results(keyword)
    
    async def _search_with_serpapi(self, keyword: str, num_results: int = 10) -> List[Dict]:
        """Use SerpAPI to get real Google search results"""
        results = []
        
        print(f"🔍 Searching Google via SerpAPI for: {keyword}")
        
        # SerpAPI endpoint
        url = "https://serpapi.com/search"
        
        params = {
            "api_key": self.serp_api_key,
            "q": keyword,
            "num": num_results,
            "engine": "google"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            print(f"✅ Got response from SerpAPI")
            
            if "organic_results" in data:
                for idx, item in enumerate(data["organic_results"], 1):
                    result_data = {
                        "position": item.get("position", idx),
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    }
                    results.append(result_data)
                    print(f"  #{result_data['position']}: {result_data['url'][:50]}...")
                
                print(f"✅ Successfully retrieved {len(results)} results from SerpAPI")
            else:
                print("⚠️  No organic results found in API response")
        
        return results
    
    def _get_mock_results(self, keyword: str) -> List[Dict]:
        """Generate mock search results for testing"""
        print(f"🎭 Using MOCK data for keyword: {keyword}")
        print(f"💡 Tip: Add SERP_API_KEY to .env for real Google results")
        print(f"   Get your free API key at: https://serpapi.com/")
        
        # Mock results based on common keywords
        mock_data = {
            "python": [
                {"position": 1, "url": "https://www.python.org", "title": "Welcome to Python.org", "snippet": "The official home of the Python Programming Language"},
                {"position": 2, "url": "https://en.wikipedia.org/wiki/Python_(programming_language)", "title": "Python (programming language) - Wikipedia", "snippet": "Python is a high-level, general-purpose programming language"},
                {"position": 3, "url": "https://www.w3schools.com/python/", "title": "Python Tutorial - W3Schools", "snippet": "Well organized and easy to understand Web building tutorials"},
                {"position": 4, "url": "https://docs.python.org/3/", "title": "Python 3 Documentation", "snippet": "Official Python documentation"},
                {"position": 5, "url": "https://realpython.com", "title": "Real Python Tutorials", "snippet": "Learn Python online with Real Python"},
            ],
            "off market real estate deals": [
                {"position": 1, "url": "https://www.zillow.com/off-market", "title": "Off Market Properties | Zillow", "snippet": "Find off-market real estate deals"},
                {"position": 2, "url": "https://www.realtor.com/off-market", "title": "Off Market Homes for Sale", "snippet": "Browse off-market properties"},
                {"position": 3, "url": "https://offa.com", "title": "Offa - Off Market Real Estate Platform", "snippet": "The best platform for off-market real estate deals"},
                {"position": 4, "url": "https://www.redfin.com/off-market", "title": "Off Market Listings | Redfin", "snippet": "Discover off-market opportunities"},
                {"position": 5, "url": "https://www.trulia.com", "title": "Trulia Real Estate", "snippet": "Find your next home"},
            ],
            "offa real estate": [
                {"position": 1, "url": "https://offa.com", "title": "Offa - Off Market Real Estate Platform", "snippet": "The best platform for off-market real estate deals"},
                {"position": 2, "url": "https://www.zillow.com", "title": "Zillow Real Estate", "snippet": "Find homes for sale"},
                {"position": 3, "url": "https://www.realtor.com", "title": "Realtor.com", "snippet": "Real estate listings"},
                {"position": 4, "url": "https://www.redfin.com", "title": "Redfin Real Estate", "snippet": "Buy and sell homes"},
                {"position": 5, "url": "https://www.trulia.com", "title": "Trulia", "snippet": "Homes for sale and rent"},
            ]
        }
        
        # Return mock data if keyword matches, otherwise generate generic results
        keyword_lower = keyword.lower()
        if keyword_lower in mock_data:
            results = mock_data[keyword_lower]
        else:
            # Generate generic mock results
            results = [
                {"position": i, "url": f"https://example{i}.com/{keyword.replace(' ', '-')}", "title": f"Result {i} for {keyword}", "snippet": f"This is a mock result for '{keyword}'. Add SERP_API_KEY to get real results."}
                for i in range(1, 6)
            ]
        
        print(f"✅ Generated {len(results)} mock results")
        return results

