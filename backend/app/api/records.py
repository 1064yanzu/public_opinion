"""Data record routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.dataset import DataSet
from ..models.record import DataRecord
from ..models.user import User
from ..schemas.record import DataRecordCreate, DataRecordRead, DataRecordBulkCreate, DataRecordBulkResponse
from ..core.deps import get_current_active_user
from ..services.nlp_service import NLPService
from ..utils.activity_logger import log_activity
from ..utils.background_tasks import ingest_records_task

router = APIRouter()


@router.post("/", response_model=DataRecordRead)
def create_record(
    record_in: DataRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a single record"""
    dataset = db.query(DataSet).filter(DataSet.id == record_in.dataset_id, DataSet.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    score, label = NLPService.analyze_sentiment(record_in.content)
    record = DataRecord(
        dataset_id=record_in.dataset_id,
        post_id=record_in.post_id,
        content=record_in.content,
        author=record_in.author,
        publish_time=record_in.publish_time,
        likes=record_in.likes,
        shares=record_in.shares,
        comments=record_in.comments,
        sentiment_score=score,
        sentiment_label=label,
    )
    db.add(record)
    dataset.total_records += 1
    db.commit()
    db.refresh(record)
    return record


@router.post("/bulk", response_model=DataRecordBulkResponse)
def create_records_bulk(
    data: DataRecordBulkCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create multiple records in background"""
    dataset = db.query(DataSet).filter(DataSet.id == data.dataset_id, DataSet.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    records_data = [record.dict() for record in data.records]
    background_tasks.add_task(ingest_records_task, data.dataset_id, records_data)
    
    log_activity(db, current_user, "bulk_create_records", resource="dataset", resource_id=data.dataset_id, details=f"{len(records_data)} records")
    return DataRecordBulkResponse(
        created_count=len(records_data),
        failed_count=0,
        dataset_id=data.dataset_id,
    )


@router.get("/{record_id}", response_model=DataRecordRead)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get record by ID"""
    record = (
        db.query(DataRecord)
        .join(DataSet)
        .filter(DataRecord.id == record_id, DataSet.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete record"""
    record = (
        db.query(DataRecord)
        .join(DataSet)
        .filter(DataRecord.id == record_id, DataSet.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    dataset = db.query(DataSet).filter(DataSet.id == record.dataset_id).first()
    db.delete(record)
    if dataset:
        dataset.total_records = max(0, dataset.total_records - 1)
    db.commit()
    return {"message": "Record deleted"}
