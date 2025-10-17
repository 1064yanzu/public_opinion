"""Report generation schemas"""
from pydantic import BaseModel
from typing import List, Optional


class ReportGenerateRequest(BaseModel):
    """Report generation request"""
    dataset_id: Optional[int] = None
    depth: str = "standard"  # simple, standard, detailed
    include_sections: List[str] = ["summary", "analysis", "suggestions", "risks"]


class ReportSection(BaseModel):
    """Report section"""
    type: str
    content: str


class ReportResponse(BaseModel):
    """Complete report response"""
    type: str = "complete"
    sections: dict
    generated_at: str
