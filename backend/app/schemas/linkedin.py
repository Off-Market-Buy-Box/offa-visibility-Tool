from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LinkedInPostResponse(BaseModel):
    id: int
    result_id: str
    title: str
    snippet: Optional[str] = None
    content: Optional[str] = None
    url: str
    author: Optional[str] = None
    source: str
    keywords_matched: Optional[str] = None
    is_relevant: bool
    created_at: datetime
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
