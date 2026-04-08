from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class OutreachTarget(Base):
    """A subreddit to post to daily"""
    __tablename__ = "outreach_targets"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False, default="reddit")
    name = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    enabled = Column(Boolean, default=True)
    last_posted_at = Column(DateTime, nullable=True)
    total_posts = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class OutreachPost(Base):
    """Log of posts made to subreddits"""
    __tablename__ = "outreach_posts"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, nullable=False)
    platform = Column(String(50), nullable=False, default="reddit")
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    error = Column(Text, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
