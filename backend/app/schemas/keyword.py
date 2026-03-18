from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class KeywordBase(BaseModel):
    keyword: str
    domain: str

class KeywordCreate(KeywordBase):
    pass

class KeywordUpdate(BaseModel):
    is_active: Optional[bool] = None

class KeywordResponse(KeywordBase):
    id: int
    is_active: bool
    best_rank: Optional[int] = None  # Best (lowest number) position where domain appears
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
