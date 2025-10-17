"""Case library schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CaseBase(BaseModel):
    """Base case schema"""
    title: str
    category: str  # 政治、经济、社会、文化、突发事件等
    description: str
    date: str
    severity: str  # low, medium, high, critical


class CaseCreate(CaseBase):
    """Create case"""
    content: str
    response_strategy: str
    lessons_learned: str
    keywords: List[str] = []


class CaseUpdate(BaseModel):
    """Update case"""
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    response_strategy: Optional[str] = None
    lessons_learned: Optional[str] = None
    keywords: Optional[List[str]] = None
    severity: Optional[str] = None


class CaseRead(CaseBase):
    """Read case"""
    id: int
    content: str
    response_strategy: str
    lessons_learned: str
    keywords: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CaseSummary(BaseModel):
    """Case summary for list"""
    id: int
    title: str
    category: str
    description: str
    date: str
    severity: str
    
    class Config:
        from_attributes = True
