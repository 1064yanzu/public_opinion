"""Spider-related schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SpiderTaskCreate(BaseModel):
    """Schema for creating a spider task"""
    keyword: str = Field(..., min_length=1, max_length=100)
    platforms: List[str] = Field(..., min_items=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    precision: str = Field(default="medium")


class SpiderTaskHistory(BaseModel):
    """Spider task history record"""
    timestamp: str
    platform: str
    keyword: str
    start_date: Optional[str]
    end_date: Optional[str]
    precision: str


class SpiderTaskStatus(BaseModel):
    """Spider task status"""
    status: str
    message: str
    task_id: Optional[str] = None
    data: Optional[dict] = None


class SpiderDataRecord(BaseModel):
    """Spider crawled data record"""
    author: str
    content: str
    time: str
    shares: int
    comments: int
    likes: int
    url: str
    profile_url: Optional[str] = None
    sentiment: Optional[str] = None


class HotTopicItem(BaseModel):
    """Hot topic item"""
    rank: int
    title: str
    heat: str
    url: Optional[str] = None
    cover_image: Optional[str] = None
