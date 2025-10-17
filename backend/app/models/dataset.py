"""Dataset model for storing user data collections"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class DataSource(str, enum.Enum):
    """Data source types"""
    WEIBO = "weibo"
    DOUYIN = "douyin"
    MANUAL = "manual"
    IMPORT = "import"


class DataSet(Base):
    """Dataset model for organizing user data"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(SQLEnum(DataSource), nullable=False)
    keyword = Column(String(255), nullable=True)  # Search keyword used
    total_records = Column(Integer, default=0)
    file_path = Column(String(500), nullable=True)  # Path to CSV file
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="datasets")
    records = relationship("DataRecord", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DataSet {self.name} (user_id={self.user_id})>"
