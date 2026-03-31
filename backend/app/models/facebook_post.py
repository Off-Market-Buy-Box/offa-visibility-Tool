from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from app.core.database import Base


class FacebookPost(Base):
    __tablename__ = "facebook_posts"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    snippet = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String, nullable=False)
    author = Column(String, nullable=True)
    source = Column(String, default="facebook.com")
    keywords_matched = Column(String, nullable=True)
    is_relevant = Column(Boolean, default=True)
    agent_posted = Column(Boolean, default=False)
    agent_posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
