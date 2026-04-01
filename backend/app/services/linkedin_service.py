import hashlib
import httpx
import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.linkedin_post import LinkedInPost


class LinkedInService:
    """Service for finding LinkedIn posts via SerpAPI Google search"""

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

    async def search_linkedin(self, query: str, num: int = 50) -> List[Dict]:
        """Search Google for LinkedIn posts matching a query"""
        results = []
        full_query = f'site:linkedin.com/posts OR site:linkedin.com/pulse OR site:linkedin.com/feed/update "{query}"'

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

                    # Only keep actual post/article URLs, not profiles or company pages
                    is_post = bool(
                        re.search(r"linkedin\.com/posts/", url)
                        or re.search(r"linkedin\.com/pulse/", url)
                        or re.search(r"linkedin\.com/feed/update/", url)
                    )
                    if not is_post:
                        continue

                    # Extract author from title (LinkedIn format: "Author Name on LinkedIn: ...")
                    author = None
                    if " on LinkedIn" in title:
                        author = title.split(" on LinkedIn")[0].strip()
                    elif " | LinkedIn" in title:
                        author = title.split(" | LinkedIn")[0].strip()

                    result_id = hashlib.md5(url.encode()).hexdigest()[:16]

                    results.append({
                        "result_id": result_id,
                        "title": title,
                        "snippet": snippet,
                        "url": url,
                        "author": author,
                        "source": "linkedin.com",
                        "keywords_matched": query,
                        "is_relevant": True,
                    })
            except Exception as e:
                print(f"❌ Error searching LinkedIn via SerpAPI: {e}")

        return results

    async def monitor_linkedin(
        self, db: AsyncSession, keywords: Optional[List[str]] = None
    ) -> Dict:
        """Search LinkedIn for all configured keywords"""
        queries = keywords if keywords else self.search_queries
        all_results = []
        stats = {"queries_searched": 0, "total_found": 0, "new_saved": 0}

        for query in queries:
            print(f"🔍 Searching LinkedIn for: {query}")
            results = await self.search_linkedin(query)
            all_results.extend(results)
            stats["queries_searched"] += 1
            print(f"  ✅ '{query}': {len(results)} results")

        # Deduplicate
        seen = set()
        unique = []
        for r in all_results:
            if r["result_id"] not in seen:
                seen.add(r["result_id"])
                unique.append(r)

        stats["total_found"] = len(unique)
        stats["new_saved"] = await self.save_posts(db, unique)
        return stats

    async def save_posts(self, db: AsyncSession, posts: List[Dict]) -> int:
        """Save LinkedIn posts to database"""
        saved = 0
        for post_data in posts:
            result = await db.execute(
                select(LinkedInPost).where(
                    LinkedInPost.result_id == post_data["result_id"]
                )
            )
            if not result.scalar_one_or_none():
                db.add(LinkedInPost(**post_data))
                saved += 1
        await db.commit()
        return saved

    async def fetch_post_content(self, url: str) -> Optional[str]:
        """Try to fetch the full text content from a LinkedIn post URL"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with httpx.AsyncClient(
            headers=headers, timeout=15.0, follow_redirects=True
        ) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

                # Method 1: Extract from og:description meta tag
                og_match = re.search(
                    r'<meta\s+(?:property|name)="og:description"\s+content="([^"]*)"',
                    html,
                )
                if not og_match:
                    og_match = re.search(
                        r'content="([^"]*)"\s+(?:property|name)="og:description"',
                        html,
                    )

                # Method 2: Try JSON-LD structured data
                content = None
                ld_match = re.search(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    html,
                    re.DOTALL,
                )
                if ld_match:
                    try:
                        ld_data = json.loads(ld_match.group(1))
                        if isinstance(ld_data, dict):
                            content = ld_data.get("articleBody") or ld_data.get(
                                "description", ""
                            )
                        elif isinstance(ld_data, list):
                            for item in ld_data:
                                if isinstance(item, dict):
                                    content = item.get(
                                        "articleBody"
                                    ) or item.get("description", "")
                                    if content:
                                        break
                    except json.JSONDecodeError:
                        pass

                if not content and og_match:
                    content = og_match.group(1)

                # Method 3: Try meta description
                if not content:
                    desc_match = re.search(
                        r'<meta\s+name="description"\s+content="([^"]*)"', html
                    )
                    if desc_match:
                        content = desc_match.group(1)

                if content:
                    # Clean up HTML entities
                    content = (
                        content.replace("&amp;", "&")
                        .replace("&lt;", "<")
                        .replace("&gt;", ">")
                        .replace("&quot;", '"')
                        .replace("&#39;", "'")
                        .replace("&#x27;", "'")
                        .replace("\n", "\n")
                    )
                    return content.strip()

            except Exception as e:
                print(f"❌ Error fetching LinkedIn post content: {e}")

        return None
