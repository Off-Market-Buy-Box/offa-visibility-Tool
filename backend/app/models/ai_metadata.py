from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON
from datetime import datetime
from app.core.database import Base


class AIMetadata(Base):
    __tablename__ = "ai_metadata"

    id = Column(Integer, primary_key=True, index=True)
    reddit_mention_id = Column(Integer, ForeignKey("reddit_mentions.id", ondelete="CASCADE"), unique=True, index=True, nullable=True)
    linkedin_post_id = Column(Integer, ForeignKey("linkedin_posts.id", ondelete="CASCADE"), unique=True, index=True, nullable=True)
    intent = Column(String, nullable=True)  # question, discussion, insight, problem, opportunity
    main_topic = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    pain_points = Column(JSON, default=list)
    opportunities = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    sentiment = Column(String, nullable=True)  # positive, negative, neutral, mixed
    created_at = Column(DateTime, default=datetime.utcnow)
