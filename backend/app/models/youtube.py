"""
YouTube 数据模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class YoutubeData(Base):
    """YouTube 数据表"""
    __tablename__ = "youtube_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    video_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    author_id = Column(String(50), nullable=True)
    publish_time = Column(DateTime, nullable=True, index=True)
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)  # YouTube 无转发，固定为 0
    view_count = Column(Integer, default=0, nullable=False)
    url = Column(Text, nullable=True)
    duration = Column(String(50), nullable=True)
    province = Column(String(50), nullable=True, index=True)
    city = Column(String(50), nullable=True)
    gender = Column(String(20), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 关系
    task = relationship("Task", back_populates="youtube_data")

    def __repr__(self):
        return f"<YoutubeData(id={self.id}, video_id='{self.video_id}')>"
