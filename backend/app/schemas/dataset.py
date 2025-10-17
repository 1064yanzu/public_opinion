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


class DataSetRead(BaseModel):
    """Schema for reading dataset data"""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    source: DataSource
    source_type: str  # For frontend compatibility
    keyword: Optional[str] = None
    total_records: int
    record_count: int  # For frontend compatibility
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_orm(cls, obj):
        """Custom ORM conversion to include computed fields"""
        data = {
            'id': obj.id,
            'user_id': obj.user_id,
            'name': obj.name,
            'description': obj.description,
            'source': obj.source,
            'source_type': obj.source.value,
            'keyword': obj.keyword,
            'total_records': obj.total_records,
            'record_count': obj.total_records,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
        }
        return cls(**data)
    
    class Config:
        from_attributes = True
