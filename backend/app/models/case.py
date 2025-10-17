"""Case library model"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from ..database import Base


class Case(Base):
    """舆情案例模型"""
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    date = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    response_strategy = Column(Text, nullable=False)
    lessons_learned = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=True)  # 存储关键词列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Case {self.title}>"
