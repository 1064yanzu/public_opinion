"""Activity log model for audit trail"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class ActivityLog(Base):
    """Activity log for tracking user actions"""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # login, create_dataset, delete_dataset, etc.
    resource = Column(String(100), nullable=True)  # Resource type
    resource_id = Column(Integer, nullable=True)  # Resource ID
    details = Column(Text, nullable=True)  # Additional details in JSON format
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    def __repr__(self):
        return f"<ActivityLog {self.action} by user {self.user_id}>"
