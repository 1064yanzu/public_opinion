"""Dataset schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..models.dataset import DataSource


class DataSetBase(BaseModel):
    """Base dataset schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source: DataSource
    keyword: Optional[str] = None


class DataSetCreate(DataSetBase):
    """Schema for creating a dataset"""
    pass


class DataSetUpdate(BaseModel):
    """Schema for updating a dataset"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class DataSetRead(DataSetBase):
    """Schema for reading dataset data"""
    id: int
    user_id: int
    total_records: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
