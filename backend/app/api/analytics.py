"""Analytics routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.dataset import DataSet
from ..models.user import User
from ..schemas.analytics import AnalyticsSummary
from ..core.deps import get_current_active_user
from ..services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/{dataset_id}", response_model=AnalyticsSummary)
def dataset_analytics(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get analytics summary for a dataset"""
    dataset = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    analytics_service = AnalyticsService(db)
    return analytics_service.dataset_summary(dataset_id, current_user.id)
