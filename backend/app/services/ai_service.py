import json
import httpx
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.reddit_mention import RedditMention
from app.models.linkedin_post import LinkedInPost
from app.models.ai_metadata import AIMetadata
from app.models.generated_response import GeneratedResponse


class AIService:
    """Service for AI analysis and content generation using OpenAI API"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o-mini"

    async def _call_openai(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Make a request to OpenAI API"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured in .env")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def analyze_post(self, db: AsyncSession, mention_id: int) -> AIMetadata:
        """Analyze a Reddit post and extract structured metadata"""
        # Get the post
        result = await db.execute(
            select(RedditMention).where(RedditMention.id == mention_id)
        )
        mention = result.scalar_one_or_none()
        if not mention:
            raise ValueError(f"Mention {mention_id} not found")

        # Check if already analyzed
        existing = await db.execute(
            select(AIMetadata).where(AIMetadata.reddit_mention_id == mention_id)
        )
        existing_meta = existing.scalar_one_or_none()
        if existing_meta:
            return existing_meta

        prompt = f"""Analyze this Reddit post and return a JSON object with the following fields:
- intent: one of "question", "discussion", "insight", "problem", "opportunity"
- main_topic: a short phrase describing the main topic
- summary: 1-2 sentence summary
- pain_points: array of pain points mentioned (max 5)
- opportunities: array of business/engagement opportunities (max 5)
- keywords: array of relevant keywords (max 8)
- sentiment: one of "positive", "negative", "neutral", "mixed"

Post title: {mention.title}
Subreddit: r/{mention.subreddit}
Content: {mention.content or 'No text content'}

Return ONLY valid JSON, no markdown formatting."""

        raw = await self._call_openai(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        # Parse JSON from response
        try:
            # Strip markdown code fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = {
                "intent": "discussion",
                "main_topic": "unknown",
                "summary": raw[:200],
                "pain_points": [],
                "opportunities": [],
                "keywords": [],
                "sentiment": "neutral",
            }

        metadata = AIMetadata(
            reddit_mention_id=mention_id,
            intent=parsed.get("intent", "discussion"),
            main_topic=parsed.get("main_topic", ""),
            summary=parsed.get("summary", ""),
            pain_points=parsed.get("pain_points", []),
            opportunities=parsed.get("opportunities", []),
            keywords=parsed.get("keywords", []),
            sentiment=parsed.get("sentiment", "neutral"),
        )
        db.add(metadata)
        await db.commit()
        await db.refresh(metadata)
        return metadata

    async def generate_response(self, db: AsyncSession, mention_id: int) -> GeneratedResponse:
        """Generate a natural community response for a Reddit post"""
        result = await db.execute(
            select(RedditMention).where(RedditMention.id == mention_id)
        )
        mention = result.scalar_one_or_none()
        if not mention:
            raise ValueError(f"Mention {mention_id} not found")

        # Get AI analysis if available
        meta_result = await db.execute(
            select(AIMetadata).where(AIMetadata.reddit_mention_id == mention_id)
        )
        metadata = meta_result.scalar_one_or_none()

        context = ""
        if metadata:
            context = f"\nAI Analysis - Intent: {metadata.intent}, Topic: {metadata.main_topic}, Sentiment: {metadata.sentiment}"

        prompt = f"""Write a short Reddit comment replying to this post. 2-3 sentences MAX, like a real person typing fast.

KNOW THIS (don't dump it, just use if relevant): Offa = off-market real estate app, like Tinder for wholesale deals. Free, has AI matching, 100% financing options.

Rules:
- 2-3 sentences ONLY. No paragraphs. Short and punchy like real Reddit comments.
- Sound like a normal dude on Reddit, not a copywriter
- Mention Offa casually in ONE sentence max — like "been using Offa for off-market stuff" or "my buddy found deals on Offa" — keep it throwaway, not the point of your comment
- Give actual helpful advice first, Offa mention is secondary
- No links, no "check out", no sales language
- Use casual language, contractions, lowercase energy

Post: {mention.title}
r/{mention.subreddit}
{mention.content or 'No text content'}{context}"""

        content = await self._call_openai(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        gen_response = GeneratedResponse(
            reddit_mention_id=mention_id,
            response_type="comment",
            content=content.strip(),
        )
        db.add(gen_response)
        await db.commit()
        await db.refresh(gen_response)
        return gen_response

    async def generate_blog(
        self, db: AsyncSession, mention_ids: List[int], topic: Optional[str] = None
    ) -> GeneratedResponse:
        """Generate a blog post from one or more Reddit discussions"""
        posts_context = []
        first_mention_id = mention_ids[0]

        for mid in mention_ids:
            result = await db.execute(
                select(RedditMention).where(RedditMention.id == mid)
            )
            mention = result.scalar_one_or_none()
            if mention:
                posts_context.append(
                    f"Title: {mention.title}\nSubreddit: r/{mention.subreddit}\nContent: {(mention.content or '')[:500]}"
                )

        if not posts_context:
            raise ValueError("No valid mentions found")

        topic_instruction = f'The blog should focus on: "{topic}"' if topic else "Determine the best topic from the discussions."

        prompt = f"""Write a blog post based on these Reddit discussions about real estate.

{topic_instruction}

Discussions:
{'---'.join(posts_context)}

Requirements:
- Professional but approachable tone
- Include insights from the community discussions
- 500-800 words
- Include a compelling title at the top
- Add practical takeaways
- Do NOT mention Reddit or specific usernames"""

        content = await self._call_openai(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        blog = GeneratedResponse(
            reddit_mention_id=first_mention_id,
            response_type="blog",
            content=content.strip(),
        )
        db.add(blog)
        await db.commit()
        await db.refresh(blog)
        return blog

    async def get_metadata(self, db: AsyncSession, mention_id: int) -> Optional[AIMetadata]:
        """Get existing AI metadata for a mention"""
        result = await db.execute(
            select(AIMetadata).where(AIMetadata.reddit_mention_id == mention_id)
        )
        return result.scalar_one_or_none()

    async def get_responses(self, db: AsyncSession, mention_id: int) -> List[GeneratedResponse]:
        """Get all generated responses for a mention"""
        result = await db.execute(
            select(GeneratedResponse)
            .where(GeneratedResponse.reddit_mention_id == mention_id)
            .order_by(GeneratedResponse.created_at.desc())
        )
        return result.scalars().all()

    async def score_relevance_batch(self, posts: list[dict]) -> list[dict]:
        """
        Use AI to score a batch of Reddit posts for relevance to Offa.
        Returns the same list with 'ai_relevant' (bool) and 'ai_relevance_reason' added.
        Processes up to ~20 posts per API call to save tokens.
        """
        if not posts:
            return posts

        # Build a compact summary of each post for the AI
        summaries = []
        for i, p in enumerate(posts):
            title = (p.get("title") or "")[:120]
            content = (p.get("content") or "")[:200]
            sub = p.get("subreddit", "")
            summaries.append(f"{i}|r/{sub}|{title}|{content}")

        batch_text = "\n".join(summaries)

        prompt = f"""You are a relevance filter for Offa, an off-market real estate marketplace (wholesale deals, pocket listings, properties not on MLS).

Score each post below. A post is RELEVANT if someone reading it could naturally benefit from hearing about off-market real estate deals, wholesale properties, or real estate investing tools. 

Posts about these topics ARE relevant:
- Buying/selling property, real estate investing, finding deals
- Wholesale real estate, off-market, pocket listings, MLS frustrations
- First-time home buying, house hunting, property search
- Flipping houses, rental properties, landlord topics
- Real estate market conditions, housing prices
- Commercial real estate, multifamily investing

Posts about these topics are NOT relevant:
- Personal finance unrelated to real estate (taxes, budgeting, retirement, scholarships)
- Stock market investing with no real estate angle
- Insurance, credit cards, student loans
- Career advice, salary negotiation
- General life advice

For each post, return ONLY a JSON array of objects with:
- "i": the post index number
- "r": true if relevant, false if not

Posts:
{batch_text}

Return ONLY a JSON array like: [{{"i":0,"r":true}},{{"i":1,"r":false}}]"""

        try:
            raw = await self._call_openai(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            scores = json.loads(cleaned)
            score_map = {s["i"]: s["r"] for s in scores}
        except Exception as e:
            print(f"⚠️ AI relevance scoring failed: {e}, marking all as relevant")
            score_map = {i: True for i in range(len(posts))}

        for i, p in enumerate(posts):
            p["is_relevant"] = score_map.get(i, True)

        return posts

    # ---- LinkedIn AI methods ----

    async def analyze_linkedin_post(self, db: AsyncSession, post_id: int) -> AIMetadata:
        """Analyze a LinkedIn post and extract structured metadata"""
        result = await db.execute(
            select(LinkedInPost).where(LinkedInPost.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            raise ValueError(f"LinkedIn post {post_id} not found")

        # Check if already analyzed
        existing = await db.execute(
            select(AIMetadata).where(AIMetadata.linkedin_post_id == post_id)
        )
        existing_meta = existing.scalar_one_or_none()
        if existing_meta:
            return existing_meta

        text = post.content or post.snippet or ""
        # Limit content to ~6000 chars for the prompt
        if len(text) > 6000:
            text = text[:6000] + "..."

        prompt = f"""Analyze this LinkedIn post and return a JSON object with the following fields:
- intent: one of "question", "discussion", "insight", "problem", "opportunity"
- main_topic: a short phrase describing the main topic
- summary: 1-2 sentence summary
- pain_points: array of pain points mentioned (max 5)
- opportunities: array of business/engagement opportunities (max 5)
- keywords: array of relevant keywords (max 8)
- sentiment: one of "positive", "negative", "neutral", "mixed"

Post title: {post.title}
Author: {post.author or 'Unknown'}
Content: {text}

Return ONLY valid JSON, no markdown formatting."""

        raw = await self._call_openai(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = {
                "intent": "discussion",
                "main_topic": "unknown",
                "summary": raw[:200],
                "pain_points": [],
                "opportunities": [],
                "keywords": [],
                "sentiment": "neutral",
            }

        metadata = AIMetadata(
            linkedin_post_id=post_id,
            intent=parsed.get("intent", "discussion"),
            main_topic=parsed.get("main_topic", ""),
            summary=parsed.get("summary", ""),
            pain_points=parsed.get("pain_points", []),
            opportunities=parsed.get("opportunities", []),
            keywords=parsed.get("keywords", []),
            sentiment=parsed.get("sentiment", "neutral"),
        )
        db.add(metadata)
        await db.commit()
        await db.refresh(metadata)
        return metadata

    async def generate_linkedin_response(self, db: AsyncSession, post_id: int) -> GeneratedResponse:
        """Generate a professional response for a LinkedIn post"""
        result = await db.execute(
            select(LinkedInPost).where(LinkedInPost.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            raise ValueError(f"LinkedIn post {post_id} not found")

        # Get AI analysis if available
        meta_result = await db.execute(
            select(AIMetadata).where(AIMetadata.linkedin_post_id == post_id)
        )
        metadata = meta_result.scalar_one_or_none()

        context = ""
        if metadata:
            context = f"\nAI Analysis - Intent: {metadata.intent}, Topic: {metadata.main_topic}, Sentiment: {metadata.sentiment}"

        text = post.content or post.snippet or ""
        if len(text) > 6000:
            text = text[:6000] + "..."

        prompt = f"""Generate a professional LinkedIn comment response to this post.

BACKGROUND KNOWLEDGE (use naturally, do NOT dump this info):
Offa is an off-market real estate marketplace — often described as a Tinder-style platform for wholesale real estate deals. It connects buyers and sellers for off-market properties not listed on the MLS. Wholesalers list deals privately, buyers browse thousands of exclusive off-market properties across the US. It's free to use, has a mobile app, and uses AI to match properties to interested buyers. They also offer up to 100% financing options. Hundreds of new deals are added nationwide every week.

You are a real estate professional who has experience with off-market deals and the industry. Use the "sandwich" technique:
1. OPEN with a thoughtful, insightful comment that adds real value to the discussion
2. MIDDLE: Naturally weave in a mention of "Offa" as a platform you've personally used or discovered — like "I've been exploring off-market opportunities through Offa and the quality of deals has been impressive" or "One thing that shifted my approach was finding platforms like Offa that focus specifically on off-market inventory" — make it sound like genuine professional experience. You can reference specific things about Offa that are relevant (like the wholesale marketplace, the AI matching, the free access, the financing) but only if it fits naturally.
3. CLOSE with a broader insight, takeaway, or encouragement that ties back to the original post

Critical rules:
- Do NOT include any links or URLs
- Do NOT sound like an ad — this must read like a professional sharing what's worked in their career
- Never say "check out" or "visit" or "sign up" — just mention Offa naturally as part of your professional experience
- Keep it concise (2-3 paragraphs max)
- Use professional but approachable LinkedIn tone
- Use first person ("In my experience", "What I've found", "I recently")
- The Offa mention should feel like 10-15% of the response, not the main point
- Vary the way you reference Offa — sometimes as a tool you use, sometimes as something a colleague recommended, sometimes as part of a broader market trend

Post title: {post.title}
Author: {post.author or 'Unknown'}
Content: {text}{context}

Write as a knowledgeable real estate professional sharing genuine insights."""

        content = await self._call_openai(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        gen_response = GeneratedResponse(
            linkedin_post_id=post_id,
            response_type="comment",
            content=content.strip(),
        )
        db.add(gen_response)
        await db.commit()
        await db.refresh(gen_response)
        return gen_response

    async def get_linkedin_metadata(self, db: AsyncSession, post_id: int) -> Optional[AIMetadata]:
        """Get existing AI metadata for a LinkedIn post"""
        result = await db.execute(
            select(AIMetadata).where(AIMetadata.linkedin_post_id == post_id)
        )
        return result.scalar_one_or_none()

    async def get_linkedin_responses(self, db: AsyncSession, post_id: int) -> List[GeneratedResponse]:
        """Get all generated responses for a LinkedIn post"""
        result = await db.execute(
            select(GeneratedResponse)
            .where(GeneratedResponse.linkedin_post_id == post_id)
            .order_by(GeneratedResponse.created_at.desc())
        )
        return result.scalars().all()
