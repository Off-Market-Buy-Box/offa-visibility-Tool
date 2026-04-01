from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base


class AutomationLog(Base):
    __tablename__ = "automation_logs"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False, index=True)  # reddit, linkedin, twitter, facebook
    action = Column(String, nullable=False)  # scan, comment
    posts_found = Column(Integer, default=0)
    posts_commented = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
