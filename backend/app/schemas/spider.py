"""Spider-related schemas"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from ..models.dataset import DataSource


class CrawlRequest(BaseModel):
    """Request schema for spider crawl"""
    source: DataSource
    keyword: str = Field(..., min_length=1, max_length=100)
    max_pages: int = Field(5, ge=1, le=50)
    dataset_id: Optional[int] = None
    dataset_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('keyword')
    def normalize_keyword(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Keyword cannot be empty")
        return value

    @validator('dataset_name', always=True)
    def validate_dataset(cls, value, values):
        dataset_id = values.get('dataset_id')
        if dataset_id is None and not value:
            raise ValueError("dataset_id or dataset_name must be provided")
        return value
