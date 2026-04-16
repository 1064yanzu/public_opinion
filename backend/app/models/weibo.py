"""
微博数据模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class WeiboData(Base):
    """微博数据表"""
    __tablename__ = "weibo_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    weibo_id = Column(String(50), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=True)
    user_name = Column(String(100), nullable=True)
    user_id = Column(String(50), nullable=True)
    publish_time = Column(DateTime, nullable=True, index=True)
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    url = Column(Text, nullable=True)
    gender = Column(String(20), nullable=True)
    province = Column(String(50), nullable=True, index=True)
    city = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    sentiment_score = Column(Float, nullable=True)  # 0.0-1.0
    sentiment_label = Column(String(20), nullable=True, index=True)  # positive, negative, neutral
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    task = relationship("Task", back_populates="weibo_data")
    
    def __repr__(self):
        return f"<WeiboData(id={self.id}, weibo_id='{self.weibo_id}')>"
