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

        prompt = f"""Generate a helpful, natural Reddit comment response to this post.

Rules:
- Directly address the discussion
- Provide useful insight or advice
- Sound natural and human
- Do NOT sound promotional
- Keep it concise (2-4 paragraphs max)
- Match the tone of the subreddit

Post title: {mention.title}
Subreddit: r/{mention.subreddit}
Content: {mention.content or 'No text content'}{context}

Write the response as if you are a knowledgeable community member."""

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

Rules:
- Directly address the discussion
- Provide useful insight or advice
- Sound professional but approachable (LinkedIn tone)
- Do NOT sound promotional or salesy
- Keep it concise (2-3 paragraphs max)
- Add value to the conversation

Post title: {post.title}
Author: {post.author or 'Unknown'}
Content: {text}{context}

Write the response as if you are a knowledgeable real estate professional."""

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
