from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FacebookPostResponse(BaseModel):
    id: int
    post_id: str
    title: str
    snippet: Optional[str] = None
    content: Optional[str] = None
    url: str
    author: Optional[str] = None
    source: str
    keywords_matched: Optional[str] = None
    is_relevant: bool
    agent_posted: bool = False
    agent_posted_at: Optional[datetime] = None
    created_at: datetime
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
