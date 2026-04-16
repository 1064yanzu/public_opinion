"""
抖音数据模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class DouyinData(Base):
    """抖音数据表"""
    __tablename__ = "douyin_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    video_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    author_id = Column(String(50), nullable=True)
    publish_time = Column(DateTime, nullable=True, index=True)
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    url = Column(Text, nullable=True)
    followers_count = Column(Integer, default=0, nullable=False)
    province = Column(String(50), nullable=True, index=True)
    city = Column(String(50), nullable=True)
    gender = Column(String(20), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    task = relationship("Task", back_populates="douyin_data")
    
    def __repr__(self):
        return f"<DouyinData(id={self.id}, video_id='{self.video_id}')>"
