from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from datetime import datetime
from app.core.database import Base

class RedditMention(Base):
    __tablename__ = "reddit_mentions"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String, unique=True, index=True, nullable=False)
    subreddit = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String)
    content = Column(Text)
    url = Column(String)
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.0)
    keywords_matched = Column(String)
    is_relevant = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime)
