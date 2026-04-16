"""
任务数据模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    task_type = Column(String(50), nullable=False)  # 'weibo', 'douyin', etc.
    keyword = Column(String(200), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    # status: pending, processing, completed, failed, cancelled
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    max_page = Column(Integer, default=10, nullable=False)
    config = Column(JSON, nullable=True)  # 额外配置参数
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="tasks")
    weibo_data = relationship("WeiboData", back_populates="task", cascade="all, delete-orphan")
    douyin_data = relationship("DouyinData", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, type='{self.task_type}', keyword='{self.keyword}', status='{self.status}')>"
