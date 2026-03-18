import httpx
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.reddit_mention import RedditMention

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
            "realestate",
            "investing",
            "personalfinance",
            "Flipping"
        ]
    
    async def search_reddit(
        self,
        query: str,
        subreddit: str = None,
        sort: str = "relevance",
        limit: int = 25
    ) -> List[Dict]:
        """Search Reddit using the search API - much better for finding relevant posts"""
        results = []
        
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
            try:
                if subreddit:
                    url = f"{self.base_url}/r/{subreddit}/search.json"
                    params = {"q": query, "restrict_sr": "on", "sort": sort, "limit": limit, "t": "month"}
                else:
                    url = f"{self.base_url}/search.json"
                    params = {"q": query, "sort": sort, "limit": limit, "t": "month"}
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    pd = post.get("data", {})
                    results.append({
                        "post_id": pd.get("id"),
                        "subreddit": pd.get("subreddit", ""),
                        "title": pd.get("title", ""),
                        "author": pd.get("author", "[deleted]"),
                        "content": pd.get("selftext", "")[:2000],
                        "url": f"{self.base_url}{pd.get('permalink', '')}",
                        "score": pd.get("score", 0),
                        "num_comments": pd.get("num_comments", 0),
                        "keywords_matched": query,
                        "posted_at": datetime.fromtimestamp(pd.get("created_utc", 0)),
                        "is_relevant": True
                    })
                    
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

    async def search_subreddit(
        self, 
        subreddit: str, 
        keywords: List[str],
        limit: int = 25
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
        limit_per_subreddit: int = 25
    ) -> Dict:
        """Monitor real estate subreddits using Reddit search API"""
        
        # Search queries that will find relevant posts
        search_queries = [
            "off market real estate",
            "off market deals",
            "wholesale real estate",
            "pocket listing",
            "real estate investing deals",
            "off market properties"
        ]
        
        if keywords:
            search_queries = keywords
        
        all_mentions = []
        stats = {
            "subreddits_checked": 0,
            "total_mentions_found": 0,
            "new_mentions_saved": 0,
            "offa_mentions": 0
        }
        
        # Search across real estate subreddits
        for subreddit in self.real_estate_subreddits:
            print(f"🔍 Searching r/{subreddit}...")
            
            for query in search_queries:
                results = await self.search_reddit(query, subreddit=subreddit, limit=limit_per_subreddit)
                
                if results:
                    all_mentions.extend(results)
                    stats["total_mentions_found"] += len(results)
                    
                    offa_count = sum(1 for m in results if "offa" in (m.get("content", "") + m.get("title", "")).lower())
                    stats["offa_mentions"] += offa_count
                    
                    print(f"  ✅ '{query}': {len(results)} results")
            
            stats["subreddits_checked"] += 1
        
        # Deduplicate
        seen = set()
        unique_mentions = []
        for m in all_mentions:
            if m["post_id"] not in seen:
                seen.add(m["post_id"])
                unique_mentions.append(m)
        
        stats["total_mentions_found"] = len(unique_mentions)
        stats["new_mentions_saved"] = await self.save_mentions(db, unique_mentions)
        
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
