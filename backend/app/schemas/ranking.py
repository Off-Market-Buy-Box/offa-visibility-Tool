from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class RankingBase(BaseModel):
    keyword_id: int
    position: int
    url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None

class RankingCreate(RankingBase):
    extra_data: Optional[Dict[str, Any]] = {}

class RankingResponse(RankingBase):
    id: int
    extra_data: Dict[str, Any]
    checked_at: datetime
    
    class Config:
        from_attributes = True
