"""
热点数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Hotspot(Base):
    """热点数据表"""
    __tablename__ = "hotspots"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    source = Column(String(100), nullable=True, index=True)
    link = Column(Text, nullable=True)
    cover_image = Column(Text, nullable=True)
    publish_date = Column(Date, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Hotspot(id={self.id}, title='{self.title[:30]}...')>"
