from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CompetitorBase(BaseModel):
    domain: str
    name: Optional[str] = None

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class CompetitorResponse(CompetitorBase):
    id: int
    visibility_score: float
    avg_position: float
    total_keywords: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
