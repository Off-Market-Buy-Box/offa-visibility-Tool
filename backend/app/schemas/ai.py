from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AIMetadataResponse(BaseModel):
    id: int
    reddit_mention_id: Optional[int] = None
    linkedin_post_id: Optional[int] = None
    twitter_post_id: Optional[int] = None
    intent: Optional[str] = None
    main_topic: Optional[str] = None
    summary: Optional[str] = None
    pain_points: List[str] = []
    opportunities: List[str] = []
    keywords: List[str] = []
    sentiment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratedResponseOut(BaseModel):
    id: int
    reddit_mention_id: Optional[int] = None
    linkedin_post_id: Optional[int] = None
    twitter_post_id: Optional[int] = None
    response_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    mention_id: int


class AnalyzeLinkedInRequest(BaseModel):
    post_id: int


class GenerateResponseRequest(BaseModel):
    mention_id: int


class GenerateLinkedInResponseRequest(BaseModel):
    post_id: int


class GenerateBlogRequest(BaseModel):
    mention_ids: List[int]
    topic: Optional[str] = None


class AnalyzeTwitterRequest(BaseModel):
    post_id: int


class GenerateTwitterResponseRequest(BaseModel):
    post_id: int
