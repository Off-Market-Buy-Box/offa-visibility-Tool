import hashlib
import httpx
import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.twitter_post import TwitterPost


class TwitterService:
    """Service for finding Twitter/X posts via SerpAPI Google search"""

    def __init__(self):
        self.api_key = settings.SERP_API_KEY
        self.search_url = "https://serpapi.com/search"
        self.search_queries = [
            "off market real estate",
            "off market deals",
            "wholesale real estate",
            "pocket listing",
            "real estate investing",
            "off market properties",
            "motivated seller real estate",
            "distressed property deals",
            "investment property for sale",
            "fix and flip opportunity",
            "real estate wholesale deal",
            "below market value property",
        ]

    async def search_twitter(self, query: str, num: int = 50) -> List[Dict]:
        """Search Google for Twitter/X posts matching a query"""
        results = []
        full_query = f'site:twitter.com/*/status OR site:x.com/*/status "{query}"'

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.search_url,
                    params={
                        "engine": "google",
                        "q": full_query,
                        "api_key": self.api_key,
                        "num": num,
                    },
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("organic_results", []):
                    url = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")

                    # Only keep actual post URLs (must contain /status/)
                    # This filters out profile pages like twitter.com/username
                    is_post = bool(
                        re.search(r"twitter\.com/[^/]+/status/\d+", url)
                        or re.search(r"x\.com/[^/]+/status/\d+", url)
                    )
                    if not is_post:
                        continue

                    # Extract author from URL
                    author = None
                    for pattern in [
                        r"twitter\.com/([^/]+)/status",
                        r"x\.com/([^/]+)/status",
                    ]:
                        match = re.search(pattern, url)
                        if match:
                            author = f"@{match.group(1)}"
                            break
                    if not author and " on X:" in title:
                        author = title.split(" on X:")[0].strip()
                    elif not author and " on Twitter:" in title:
                        author = title.split(" on Twitter:")[0].strip()

                    tweet_id = hashlib.md5(url.encode()).hexdigest()[:16]

                    results.append({
                        "tweet_id": tweet_id,
                        "title": title,
                        "snippet": snippet,
                        "url": url,
                        "author": author,
                        "source": "twitter.com",
                        "keywords_matched": query,
                        "is_relevant": True,
                    })
            except Exception as e:
                print(f"❌ Error searching Twitter via SerpAPI: {e}")

        return results

    async def monitor_twitter(
        self, db: AsyncSession, keywords: Optional[List[str]] = None
    ) -> Dict:
        """Search Twitter for all configured keywords"""
        queries = keywords if keywords else self.search_queries
        all_results = []
        stats = {"queries_searched": 0, "total_found": 0, "new_saved": 0}

        for query in queries:
            print(f"🔍 Searching Twitter for: {query}")
            results = await self.search_twitter(query)
            all_results.extend(results)
            stats["queries_searched"] += 1
            print(f"  ✅ '{query}': {len(results)} results")

        # Deduplicate
        seen = set()
        unique = []
        for r in all_results:
            if r["tweet_id"] not in seen:
                seen.add(r["tweet_id"])
                unique.append(r)

        stats["total_found"] = len(unique)
        stats["new_saved"] = await self.save_posts(db, unique)
        return stats

    async def save_posts(self, db: AsyncSession, posts: List[Dict]) -> int:
        """Save Twitter posts to database"""
        saved = 0
        for post_data in posts:
            result = await db.execute(
                select(TwitterPost).where(
                    TwitterPost.tweet_id == post_data["tweet_id"]
                )
            )
            if not result.scalar_one_or_none():
                db.add(TwitterPost(**post_data))
                saved += 1
        await db.commit()
        return saved

    async def fetch_post_content(self, url: str) -> Optional[str]:
        """Try to fetch tweet content from the URL"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }

        async with httpx.AsyncClient(
            headers=headers, timeout=15.0, follow_redirects=True
        ) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

                og_match = re.search(
                    r'<meta\s+(?:property|name)="og:description"\s+content="([^"]*)"',
                    html,
                )
                if not og_match:
                    og_match = re.search(
                        r'content="([^"]*)"\s+(?:property|name)="og:description"',
                        html,
                    )

                if og_match:
                    content = og_match.group(1)
                    content = (
                        content.replace("&amp;", "&")
                        .replace("&lt;", "<")
                        .replace("&gt;", ">")
                        .replace("&quot;", '"')
                        .replace("&#39;", "'")
                    )
                    return content.strip()
            except Exception as e:
                print(f"❌ Error fetching tweet content: {e}")

        return None
