"""Dataset routes"""
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
from ..database import get_db
from ..models.dataset import DataSet, DataSource
from ..models.user import User
from ..models.record import DataRecord
from ..schemas.dataset import DataSetRead, DataSetCreate, DataSetUpdate
from ..schemas.record import DataRecordBase, DataRecordRead
from ..core.deps import get_current_active_user
from ..config import get_settings
from ..services.nlp_service import NLPService
from ..utils.activity_logger import log_activity

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=List[DataSetRead])
def list_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List datasets for the current user"""
    datasets = (
        db.query(DataSet)
        .filter(DataSet.user_id == current_user.id)
        .order_by(DataSet.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return datasets


@router.post("/", response_model=DataSetRead)
def create_dataset(
    dataset_in: DataSetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new dataset"""
    dataset = DataSet(
        user_id=current_user.id,
        name=dataset_in.name,
        description=dataset_in.description,
        source=dataset_in.source,
        keyword=dataset_in.keyword,
        total_records=0,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    log_activity(db, current_user, "create_dataset", resource="dataset", resource_id=dataset.id)
    return dataset


@router.get("/{dataset_id}", response_model=DataSetRead)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get dataset by ID"""
    dataset = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.put("/{dataset_id}", response_model=DataSetRead)
def update_dataset(
    dataset_id: int,
    dataset_in: DataSetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update dataset"""
    dataset = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    update_data = dataset_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dataset, key, value)
    
    db.commit()
    db.refresh(dataset)
    
    log_activity(db, current_user, "update_dataset", resource="dataset", resource_id=dataset.id)
    return dataset


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete dataset"""
    dataset = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    db.delete(dataset)
    db.commit()
    
    log_activity(db, current_user, "delete_dataset", resource="dataset", resource_id=dataset_id)
    return {"message": "Dataset deleted"}


@router.post("/{dataset_id}/upload", response_model=DataSetRead)
def upload_dataset_file(
    dataset_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload dataset file and ingest records"""
    dataset = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    allowed_extensions = {"csv", "xlsx"}
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    file_path = Path(settings.UPLOAD_DIR) / f"user_{current_user.id}" / str(dataset_id)
    file_path.mkdir(parents=True, exist_ok=True)
    saved_file = file_path / file.filename
    with open(saved_file, "wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
    
    dataset.file_path = str(saved_file)
    db.commit()
    db.refresh(dataset)
    
    # Optionally ingest data from file (load into records)
    try:
        if file_extension == "csv":
            df = pd.read_csv(saved_file)
        else:
            df = pd.read_excel(saved_file)
        
        records_added = 0
        for _, row in df.iterrows():
            content = row.get("content") or row.get("text") or ""
            score, label = NLPService.analyze_sentiment(content)
            record = DataRecord(
                dataset_id=dataset_id,
                content=content,
                author=row.get("author"),
                publish_time=row.get("publish_time"),
                likes=int(row.get("likes", 0) or 0),
                shares=int(row.get("shares", 0) or 0),
                comments=int(row.get("comments", 0) or 0),
                sentiment_score=score,
                sentiment_label=label,
            )
            db.add(record)
            records_added += 1
        
        dataset.total_records += records_added
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to ingest file: {str(e)}")
    
    log_activity(db, current_user, "upload_dataset", resource="dataset", resource_id=dataset_id, details=str(saved_file))
    return dataset


@router.get("/{dataset_id}/records", response_model=List[DataRecordRead])
def list_records(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List records for a dataset"""
    dataset = db.query(DataSet).filter(DataSet.id == dataset_id, DataSet.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    records = (
        db.query(DataRecord)
        .filter(DataRecord.dataset_id == dataset_id)
        .order_by(DataRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records
