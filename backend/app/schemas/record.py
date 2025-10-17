"""Data record schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DataRecordBase(BaseModel):
    """Base data record schema"""
    post_id: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    publish_time: Optional[datetime] = None
    likes: int = 0
    shares: int = 0
    comments: int = 0


class DataRecordCreate(DataRecordBase):
    """Schema for creating a data record"""
    dataset_id: int


class DataRecordRead(DataRecordBase):
    """Schema for reading data record"""
    id: int
    dataset_id: int
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DataRecordBulkCreate(BaseModel):
    """Schema for bulk creating records"""
    dataset_id: int
    records: List[DataRecordBase]


class DataRecordBulkResponse(BaseModel):
    """Response for bulk create"""
    created_count: int
    failed_count: int
    dataset_id: int
