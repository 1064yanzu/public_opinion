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
    sentiment: Optional[str] = None  # For frontend compatibility
    source_url: Optional[str] = None  # For frontend compatibility
    published_at: Optional[datetime] = None  # For frontend compatibility
    created_at: datetime
    
    @classmethod
    def from_orm(cls, obj):
        """Custom ORM conversion to include computed fields"""
        data = {
            'id': obj.id,
            'dataset_id': obj.dataset_id,
            'post_id': obj.post_id,
            'content': obj.content,
            'author': obj.author,
            'publish_time': obj.publish_time,
            'published_at': obj.publish_time,  # Alias
            'likes': obj.likes,
            'shares': obj.shares,
            'comments': obj.comments,
            'sentiment_score': obj.sentiment_score,
            'sentiment_label': obj.sentiment_label,
            'sentiment': obj.sentiment_label,  # Alias
            'source_url': None,  # Not stored currently
            'created_at': obj.created_at,
        }
        return cls(**data)
    
    class Config:
        from_attributes = True


class DataRecordBulkCreate(BaseModel):
    """Schema for bulk creating records"""
    dataset_id: int
    records: Optional[List[DataRecordBase]] = None
    contents: Optional[List[str]] = None  # Alternative: just list of strings


class DataRecordBulkResponse(BaseModel):
    """Response for bulk create"""
    created_count: int
    failed_count: int
    dataset_id: int
