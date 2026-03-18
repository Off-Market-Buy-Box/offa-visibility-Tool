from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RedditMentionBase(BaseModel):
    subreddit: str
    title: str
    keywords_matched: Optional[str] = None

class RedditMentionCreate(RedditMentionBase):
    post_id: str
    author: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    score: Optional[int] = 0
    num_comments: Optional[int] = 0
    posted_at: Optional[datetime] = None

class RedditMentionResponse(RedditMentionBase):
    id: int
    post_id: str
    author: Optional[str]
    content: Optional[str]
    url: Optional[str]
    score: int
    num_comments: int
    sentiment_score: float
    is_relevant: bool
    created_at: datetime
    posted_at: Optional[datetime]
    
    class Config:
        from_attributes = True
