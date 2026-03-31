from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime
from app.core.database import Base


class GeneratedResponse(Base):
    __tablename__ = "generated_responses"

    id = Column(Integer, primary_key=True, index=True)
    reddit_mention_id = Column(Integer, ForeignKey("reddit_mentions.id", ondelete="CASCADE"), index=True, nullable=True)
    linkedin_post_id = Column(Integer, ForeignKey("linkedin_posts.id", ondelete="CASCADE"), index=True, nullable=True)
    twitter_post_id = Column(Integer, ForeignKey("twitter_posts.id", ondelete="CASCADE"), index=True, nullable=True)
    facebook_post_id = Column(Integer, ForeignKey("facebook_posts.id", ondelete="CASCADE"), index=True, nullable=True)
    response_type = Column(String, nullable=False)  # "comment", "blog"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
