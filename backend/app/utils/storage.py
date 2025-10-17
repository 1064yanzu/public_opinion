"""Storage utilities for datasets and user data"""
from pathlib import Path
from typing import List, Optional
import pandas as pd
from ..config import get_settings
from ..models.dataset import DataSet
from ..models.record import DataRecord
from sqlalchemy.orm import Session
from datetime import datetime

settings = get_settings()


def get_user_data_dir(user_id: int) -> Path:
    """Get base directory for user data"""
    base_dir = Path(settings.USER_DATA_DIR)
    user_dir = base_dir / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_dataset_dir(user_id: int, dataset_id: int) -> Path:
    """Get directory for dataset files"""
    dataset_dir = get_user_data_dir(user_id) / f"dataset_{dataset_id}"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    return dataset_dir


def export_dataset_to_csv(
    db: Session,
    dataset: DataSet,
    records: Optional[List[DataRecord]] = None,
    filename: str = "records.csv"
) -> Path:
    """Export dataset records to CSV file and update dataset file_path"""
    if records is None:
        records = (
            db.query(DataRecord)
            .filter(DataRecord.dataset_id == dataset.id)
            .order_by(DataRecord.created_at.asc())
            .all()
        )
    
    dataset_dir = get_dataset_dir(dataset.user_id, dataset.id)
    file_path = dataset_dir / filename
    
    rows = []
    for record in records:
        publish_time = None
        if record.publish_time:
            publish_time = record.publish_time.isoformat()
        rows.append({
            "post_id": record.post_id,
            "content": record.content,
            "author": record.author,
            "publish_time": publish_time,
            "likes": record.likes,
            "shares": record.shares,
            "comments": record.comments,
            "sentiment_score": record.sentiment_score,
            "sentiment_label": record.sentiment_label,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            # Chinese alias columns for compatibility
            "点赞数": record.likes,
            "评论数": record.comments,
            "分享数": record.shares,
            "情感倾向": record.sentiment_label,
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    # Update dataset file path if needed
    dataset.file_path = str(file_path)
    db.commit()
    db.refresh(dataset)
    
    return file_path
