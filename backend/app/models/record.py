"""Data record model for storing individual data points"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class DataRecord(Base):
    """Individual data record (social media post, etc.)"""
    __tablename__ = "data_records"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    
    # Post metadata
    post_id = Column(String(255), nullable=True)  # External post ID
    content = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    publish_time = Column(DateTime(timezone=True), nullable=True)
    
    # Metrics
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    
    # Analysis results
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    sentiment_label = Column(String(50), nullable=True)  # positive, negative, neutral
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    dataset = relationship("DataSet", back_populates="records")
    
    def __repr__(self):
        return f"<DataRecord {self.id} (dataset_id={self.dataset_id})>"
