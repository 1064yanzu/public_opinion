"""Background tasks for concurrent processing"""
from typing import List
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.record import DataRecord
from ..models.dataset import DataSet
from ..services.nlp_service import NLPService


def ingest_records_task(dataset_id: int, records_data: List[dict]):
    """Background task for ingesting records concurrently"""
    db: Session = SessionLocal()
    try:
        dataset = db.query(DataSet).filter(DataSet.id == dataset_id).first()
        if not dataset:
            return
        
        created = 0
        for record_data in records_data:
            content = record_data.get("content")
            score, label = NLPService.analyze_sentiment(content)
            record = DataRecord(
                dataset_id=dataset_id,
                post_id=record_data.get("post_id"),
                content=content,
                author=record_data.get("author"),
                publish_time=record_data.get("publish_time"),
                likes=record_data.get("likes", 0),
                shares=record_data.get("shares", 0),
                comments=record_data.get("comments", 0),
                sentiment_score=score,
                sentiment_label=label,
            )
            db.add(record)
            created += 1
        
        dataset.total_records += created
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
