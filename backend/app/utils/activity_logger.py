"""Activity logger for audit trail"""
from sqlalchemy.orm import Session
from fastapi import Request
from typing import Optional
from ..models.log import ActivityLog
from ..models.user import User


def log_activity(
    db: Session,
    user: User,
    action: str,
    resource: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    request: Optional[Request] = None,
):
    """Log user activity"""
    log = ActivityLog(
        user_id=user.id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log)
    db.commit()
