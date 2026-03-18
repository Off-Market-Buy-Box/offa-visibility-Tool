from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from app.core.database import Base


class LinkedInPost(Base):
    __tablename__ = "linkedin_posts"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(String, unique=True, index=True, nullable=False)  # unique hash of url
    title = Column(String, nullable=False)
    snippet = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Full text fetched from the page
    url = Column(String, nullable=False)
    author = Column(String, nullable=True)
    source = Column(String, default="linkedin.com")
    keywords_matched = Column(String, nullable=True)
    is_relevant = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
