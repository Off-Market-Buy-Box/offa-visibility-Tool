from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Ranking(Base):
    __tablename__ = "rankings"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False)
    position = Column(Integer, nullable=False)
    url = Column(String)
    title = Column(String)
    snippet = Column(String)
    extra_data = Column(JSON, default={})
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    keyword = relationship("Keyword", back_populates="rankings")
