import hashlib
import httpx
import re
import json
import random
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.config import settings
from app.models.twitter_post import TwitterPost


class TwitterService:
    """Service for finding Twitter/X posts via SerpAPI (native Twitter engine + Google fallback)"""

    def __init__(self):
        self.api_key = settings.SERP_API_KEY
        self.search_url = "https://serpapi.com/search"

        # Large pool of queries — we pick a random subset each cycle
        self.all_queries = [
            # Core off-market
            "off market real estate",
            "off market deals",
            "off market properties",
            "off market house",
            "off market property for sale",
            # Wholesale
            "wholesale real estate",
            "wholesale real estate deals",
            "wholesale property",
            "wholesaling houses",
            "real estate wholesale deal",
            # Pocket listings
            "pocket listing",
            "pocket listing real estate",
            # Investing
            "real estate investing",
            "investment property for sale",
            "real estate investor",
            "rental property deal",
            "buy and hold real estate",
            "cash flowing property",
            # Distressed / motivated
            "motivated seller real estate",
            "distressed property deals",
            "distressed property",
            "motivated seller",
            "foreclosure deal",
            "pre foreclosure",
            # Fix and flip
            "fix and flip opportunity",
            "fix and flip",
            "fixer upper for sale",
            "rehab property",
            # Below market
            "below market value property",
            "below market value",
            "undervalued property",
            # Deal-finding
            "how to find off market deals",
            "finding real estate deals",
            "real estate deal flow",
            "driving for dollars",
            "direct mail real estate",
            # Specific property types
            "multifamily deal",
            "duplex for sale investor",
            "commercial real estate deal",
            "land deal real estate",
        ]

    def _pick_queries(self, count: int = 8) -> List[str]:
        """Pick a random subset of queries each cycle for variety"""
        return random.sample(self.all_queries, min(count, len(self.all_queries)))

    async def search_twitter_native(self, query: str) -> List[Dict]:
        """Search using SerpAPI's native Twitter/X engine (searches X directly)"""
        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.search_url,
                    params={
                        "engine": "twitter",
                        "q": query,
                        "api_key": self.api_key,
                    },
                )
                response.raise_for_status()
                data = response.json()

                for tweet in data.get("timeline", {}).get("instructions", [{}]):
                    entries = tweet.get("entries", [])
                    for entry in entries:
                        content = entry.get("content", {})
                        item_content = content.get("itemContent", {})
                        tweet_results = item_content.get("tweet_results", {})
                        result = tweet_results.get("result", {})
                        legacy = result.get("legacy", {})
                        core = result.get("core", {})
                        user = core.get("user_results", {}).get("result", {}).get("legacy", {})

                        text = legacy.get("full_text", "")
                        screen_name = user.get("screen_name", "")
                        tweet_id_str = legacy.get("id_str", "")

                        if not text or not tweet_id_str:
                            continue

                        url = f"https://x.com/{screen_name}/status/{tweet_id_str}"
                        results.append({
                            "tweet_id": tweet_id_str,
                            "title": text[:120],
                            "snippet": text,
                            "url": url,
                            "author": f"@{screen_name}" if screen_name else None,
                            "source": "x.com",
                            "keywords_matched": query,
                            "is_relevant": True,
                        })

                # Also check the simpler "organic_results" format
                for item in data.get("organic_results", []):
                    url = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")

                    if not re.search(r"(twitter\.com|x\.com)/[^/]+/status/\d+", url):
                        continue

                    author = None
                    match = re.search(r"(?:twitter|x)\.com/([^/]+)/status", url)
                    if match:
                        author = f"@{match.group(1)}"

                    tweet_id = hashlib.md5(url.encode()).hexdigest()[:16]
                    results.append({
                        "tweet_id": tweet_id,
                        "title": title,
                        "snippet": snippet,
                        "url": url,
                        "author": author,
                        "source": "x.com",
                        "keywords_matched": query,
                        "is_relevant": True,
                    })

            except Exception as e:
                print(f"⚠️ Twitter native search failed for '{query}': {e}")

        return results

    async def search_twitter_google(self, query: str, num: int = 50) -> List[Dict]:
        """Fallback: Search Google for Twitter/X posts"""
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

                    is_post = bool(
                        re.search(r"twitter\.com/[^/]+/status/\d+", url)
                        or re.search(r"x\.com/[^/]+/status/\d+", url)
                    )
                    if not is_post:
                        continue

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
                print(f"❌ Error searching Twitter via Google: {e}")

        return results

    async def monitor_twitter(
        self, db: AsyncSession, keywords: Optional[List[str]] = None
    ) -> Dict:
        """Search Twitter using both native + Google engines with randomized queries"""
        queries = keywords if keywords else self._pick_queries(8)
        all_results = []
        stats = {"queries_searched": 0, "total_found": 0, "new_saved": 0}

        for query in queries:
            print(f"🔍 Searching Twitter for: {query}")

            # Try native Twitter engine first
            native_results = await self.search_twitter_native(query)
            if native_results:
                all_results.extend(native_results)
                print(f"  ✅ Native: {len(native_results)} results")

            # Also search via Google for broader coverage
            google_results = await self.search_twitter_google(query)
            if google_results:
                all_results.extend(google_results)
                print(f"  ✅ Google: {len(google_results)} results")

            stats["queries_searched"] += 1

        # Deduplicate by URL (normalized)
        seen = set()
        unique = []
        for r in all_results:
            # Normalize URL for dedup
            norm_url = r["url"].replace("twitter.com", "x.com").rstrip("/")
            key = r.get("tweet_id") or hashlib.md5(norm_url.encode()).hexdigest()[:16]
            if key not in seen:
                seen.add(key)
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
