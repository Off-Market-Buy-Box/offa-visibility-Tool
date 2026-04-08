import asyncio
import hashlib
import httpx
import random
import re
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.reddit_mention import RedditMention
from app.core.config import settings

class RedditService:
    """Service for monitoring Reddit mentions of real estate and offa.com"""
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        self.real_estate_subreddits = [
            "realestateinvesting",
            "RealEstate",
            "FirstTimeHomeBuyer",
            "CommercialRealEstate",
            "WholesaleRealestate",
            "Flipping",
            "realestate",
            "HousingMarket",
            "RealEstateAdvice",
            "Landlord",
            "PropertyManagement",
            "REBubble",
            "homeowners",
            "RealEstateCanada",
            "RealEstateTechnology",
            "realestateinvestingclub",
            "Mortgages",
            "personalfinance",
            "financialindependence",
            "fatFIRE",
            "leanfire",
            "investing",
            "passiveincome",
            "rentalincome",
            "homebuying",
            "HomeImprovement",
        ]
    
    async def search_reddit_serp(self, query: str, subreddit: str = None, num: int = 50) -> List[Dict]:
        """Search Reddit via SerpAPI Google search — no rate limits"""
        results = []
        if subreddit:
            full_query = f'site:reddit.com/r/{subreddit} "{query}"'
        else:
            full_query = f'site:reddit.com "{query}"'

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={"engine": "google", "q": full_query, "api_key": settings.SERP_API_KEY, "num": num},
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("organic_results", []):
                    url = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")

                    # Only keep actual Reddit post URLs (not user profiles, wiki, etc.)
                    if not re.search(r"reddit\.com/r/[^/]+/comments/", url):
                        continue

                    # Extract subreddit and post_id from URL
                    match = re.search(r"reddit\.com/r/([^/]+)/comments/([^/]+)", url)
                    if not match:
                        continue

                    sub_name = match.group(1)
                    post_id = match.group(2)
                    combined = (title + " " + snippet).lower()

                    results.append({
                        "post_id": post_id,
                        "subreddit": sub_name,
                        "title": title.replace(f" : r/{sub_name}", "").replace(f" : {sub_name}", "").strip(),
                        "author": "[unknown]",
                        "content": snippet,
                        "url": url.split("?")[0],
                        "score": 0,
                        "num_comments": 0,
                        "keywords_matched": query,
                        "posted_at": datetime.utcnow(),
                        "is_relevant": self._check_relevance(combined),
                    })
            except Exception as e:
                print(f"❌ Error searching Reddit via SerpAPI: {e}")

        return results

    async def search_reddit(
        self,
        query: str,
        subreddit: str = None,
        sort: str = "relevance",
        limit: int = 100,
        time_filter: str = "month",
    ) -> List[Dict]:
        """Search Reddit using the search API with pagination for more results"""
        results = []
        fetched = 0
        after = None
        # Reddit caps per-request at 100
        per_page = min(limit, 100)

        async with httpx.AsyncClient(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
            try:
                while fetched < limit:
                    if subreddit:
                        url = f"{self.base_url}/r/{subreddit}/search.json"
                        params = {"q": query, "restrict_sr": "on", "sort": sort, "limit": per_page, "t": time_filter}
                    else:
                        url = f"{self.base_url}/search.json"
                        params = {"q": query, "sort": sort, "limit": per_page, "t": time_filter}

                    if after:
                        params["after"] = after

                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])

                    if not posts:
                        break

                    for post in posts:
                        pd = post.get("data", {})
                        title = pd.get("title", "")
                        content = pd.get("selftext", "")[:2000]
                        combined = (title + " " + content).lower()

                        is_relevant = self._check_relevance(combined)

                        results.append({
                            "post_id": pd.get("id"),
                            "subreddit": pd.get("subreddit", ""),
                            "title": title,
                            "author": pd.get("author", "[deleted]"),
                            "content": content,
                            "url": f"{self.base_url}{pd.get('permalink', '')}",
                            "score": pd.get("score", 0),
                            "num_comments": pd.get("num_comments", 0),
                            "keywords_matched": query,
                            "posted_at": datetime.fromtimestamp(pd.get("created_utc", 0)),
                            "is_relevant": is_relevant,
                        })

                    fetched += len(posts)
                    after = data.get("data", {}).get("after")
                    if not after:
                        break

                    # Be polite to Reddit's rate limit
                    await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Error searching Reddit: {e}")

        return results

    async def get_post_comments(self, post_url: str, limit: int = 500) -> List[Dict]:
        """Fetch ALL comments and sub-comments for a Reddit post"""
        comments = []
        
        # Convert post URL to JSON endpoint
        json_url = post_url.rstrip("/") + ".json"
        
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(json_url, params={"limit": limit, "depth": 10})
                response.raise_for_status()
                data = response.json()
                
                # Reddit returns [post_data, comments_data]
                if len(data) >= 2:
                    comment_listing = data[1].get("data", {}).get("children", [])
                    self._extract_comments(comment_listing, comments, depth=0)
                        
            except Exception as e:
                print(f"❌ Error fetching comments: {e}")
        
        return comments

    def _extract_comments(self, children: list, comments: list, depth: int):
        """Recursively extract comments and all nested replies"""
        for comment in children:
            if comment.get("kind") != "t1":
                continue
            cd = comment.get("data", {})
            if not cd.get("body"):
                continue
            
            comments.append({
                "id": cd.get("id", ""),
                "author": cd.get("author", "[deleted]"),
                "body": cd.get("body", ""),
                "score": cd.get("score", 0),
                "depth": depth,
                "created_utc": cd.get("created_utc", 0),
                "created_at": datetime.fromtimestamp(cd.get("created_utc", 0)).isoformat()
            })
            
            # Recursively get replies
            replies = cd.get("replies")
            if replies and isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                self._extract_comments(reply_children, comments, depth=depth + 1)
        
        return comments

    def _check_relevance(self, text: str) -> bool:
        """Check if a post is actually about real estate / property investing."""
        # Must contain at least one real-estate-related keyword
        relevant_terms = [
            "real estate", "property", "properties", "house", "home",
            "rental", "landlord", "tenant", "mortgage", "wholesale",
            "off market", "off-market", "pocket listing", "mls",
            "flip", "flipping", "rehab", "investment property",
            "buy and hold", "cash flow", "cap rate", "roi",
            "deal", "closing", "under contract", "seller",
            "buyer", "listing", "appraisal", "inspection",
            "foreclosure", "distressed", "motivated seller",
            "duplex", "triplex", "multifamily", "single family",
            "condo", "apartment", "commercial", "residential",
            "offa", "zillow", "redfin", "realtor",
        ]
        return any(term in text for term in relevant_terms)

    async def search_subreddit(
        self, 
        subreddit: str, 
        keywords: List[str],
        limit: int = 100
    ) -> List[Dict]:
        """Search a subreddit for keyword mentions using search API"""
        all_results = []
        
        # Search for each keyword
        for keyword in keywords:
            results = await self.search_reddit(keyword, subreddit=subreddit, limit=limit)
            all_results.extend(results)
        
        # Deduplicate by post_id
        seen = set()
        unique = []
        for r in all_results:
            if r["post_id"] not in seen:
                seen.add(r["post_id"])
                unique.append(r)
        
        return unique

    async def monitor_real_estate_mentions(
        self,
        db: AsyncSession,
        keywords: List[str] = None,
        limit_per_subreddit: int = 100
    ) -> Dict:
        """Monitor real estate subreddits using Reddit search API + AI relevance filtering"""
        
        # Search queries focused on off-market / wholesale / property deals
        search_queries = [
            "off market deals",
            "off market properties",
            "wholesale real estate deals",
            "pocket listing",
            "finding off market",
            "wholesale deals",
            "how to find deals",
            "MLS alternatives",
            "off market house",
            "investment property deals",
        ]
        
        if keywords:
            search_queries = keywords
        
        all_mentions = []
        stats = {
            "subreddits_checked": 0,
            "total_mentions_found": 0,
            "new_mentions_saved": 0,
            "offa_mentions": 0,
            "ai_filtered_out": 0,
        }

        # Search across real estate subreddits using SerpAPI (no rate limits)
        for subreddit in self.real_estate_subreddits:
            print(f"🔍 Searching r/{subreddit}...")
            
            for query in search_queries:
                # Use SerpAPI (Google) — no Reddit rate limits
                results = await self.search_reddit_serp(query, subreddit=subreddit, num=50)
                
                if results:
                    all_mentions.extend(results)
                    print(f"  ✅ '{query}': {len(results)} results")
            
            stats["subreddits_checked"] += 1
        
        # Deduplicate by post_id
        seen = set()
        unique_mentions = []
        for m in all_mentions:
            if m["post_id"] not in seen:
                seen.add(m["post_id"])
                unique_mentions.append(m)

        # Step 1: Quick keyword filter (remove obviously irrelevant)
        keyword_filtered = [m for m in unique_mentions if m.get("is_relevant", True)]
        print(f"📋 After keyword filter: {len(keyword_filtered)}/{len(unique_mentions)} posts")

        # Step 2: AI relevance scoring on the remaining posts (batches of 20)
        from app.services.ai_service import AIService
        ai = AIService()
        ai_scored = []
        for i in range(0, len(keyword_filtered), 20):
            batch = keyword_filtered[i:i+20]
            scored = await ai.score_relevance_batch(batch)
            ai_scored.extend(scored)

        relevant = [m for m in ai_scored if m.get("is_relevant", False)]
        stats["ai_filtered_out"] = len(ai_scored) - len(relevant)
        stats["total_mentions_found"] = len(relevant)
        print(f"🤖 After AI filter: {len(relevant)}/{len(ai_scored)} posts relevant")

        # Save only relevant posts
        stats["new_mentions_saved"] = await self.save_mentions(db, relevant)
        
        return stats
    
    async def save_mentions(self, db: AsyncSession, mentions: List[Dict]) -> int:
        """Save Reddit mentions to database"""
        saved_count = 0
        
        for mention_data in mentions:
            result = await db.execute(
                select(RedditMention).where(RedditMention.post_id == mention_data["post_id"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                mention = RedditMention(**mention_data)
                db.add(mention)
                saved_count += 1
        
        await db.commit()
        return saved_count
