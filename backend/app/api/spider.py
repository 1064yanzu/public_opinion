"""Spider API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
from ..database import get_db
from ..models.user import User
from ..models.dataset import DataSet, DataSource
from ..core.deps import get_current_active_user
from ..services.spider_service import SpiderService
from ..services.nlp_service import NLPService
from ..schemas.spider import CrawlRequest
from ..utils.activity_logger import log_activity
from ..models.record import DataRecord
from ..utils.storage import export_dataset_to_csv
from datetime import datetime

router = APIRouter()


def parse_publish_time(value):
    """Parse publish time string to datetime"""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    
    return None


def crawl_and_save_task(
    dataset_id: int,
    source: str,
    keyword: str,
    max_pages: int,
):
    """Background task for crawling and saving data"""
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        spider_service = SpiderService()
        nlp_service = NLPService()
        
        # Crawl data
        raw_data = spider_service.crawl_data(source, keyword, max_pages)
        
        if not raw_data:
            print(f"No data crawled for keyword: {keyword}")
            return
        
        # Process and save records
        dataset = db.query(DataSet).filter(DataSet.id == dataset_id).first()
        if not dataset:
            return
        
        created_count = 0
        for item in raw_data:
            try:
                content = item.get('content', '')
                score, label = nlp_service.analyze_sentiment(content)
                
                post_id = item.get('post_id')
                if post_id:
                    exists = (
                        db.query(DataRecord)
                        .filter(
                            DataRecord.dataset_id == dataset_id,
                            DataRecord.post_id == post_id
                        )
                        .first()
                    )
                    if exists:
                        continue
                
                record = DataRecord(
                    dataset_id=dataset_id,
                    post_id=item.get('post_id'),
                    content=content,
                    author=item.get('author'),
                    publish_time=parse_publish_time(item.get('publish_time')),
                    likes=item.get('likes', 0),
                    shares=item.get('shares', 0),
                    comments=item.get('comments', 0),
                    sentiment_score=score,
                    sentiment_label=label,
                )
                db.add(record)
                created_count += 1
            except Exception as e:
                print(f"Error processing record: {e}")
                continue
        
        # Update dataset
        dataset.total_records += created_count
        db.commit()
        
        # Export to CSV for compatibility with legacy features
        try:
            export_dataset_to_csv(db, dataset)
            print(f"Exported dataset to CSV")
        except Exception as e:
            print(f"CSV export failed: {e}")
        
        print(f"Successfully crawled and saved {created_count} records")
    except Exception as e:
        print(f"Error in crawl task: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/crawl")
def start_crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Start a spider crawl task
    
    Creates a new dataset or uses existing one, then crawls data in background
    """
    # Get or create dataset
    if request.dataset_id:
        dataset = db.query(DataSet).filter(
            DataSet.id == request.dataset_id,
            DataSet.user_id == current_user.id
        ).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
    else:
        # Create new dataset
        dataset = DataSet(
            user_id=current_user.id,
            name=request.dataset_name or f"{request.source.value}-{request.keyword}",
            description=request.description,
            source=request.source,
            keyword=request.keyword,
            total_records=0,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
    
    # Start background crawl task
    background_tasks.add_task(
        crawl_and_save_task,
        dataset.id,
        request.source.value,
        request.keyword,
        request.max_pages
    )
    
    log_activity(
        db,
        current_user,
        "start_crawl",
        resource="dataset",
        resource_id=dataset.id,
        details=f"{request.source.value}:{request.keyword}"
    )
    
    return {
        "message": "Crawl task started",
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "estimated_records": request.max_pages * 10,  # Rough estimate
    }


@router.get("/sources")
def list_sources():
    """List available spider sources"""
    spider_service = SpiderService()
    sources = spider_service.available_sources()
    
    return {
        "sources": sources,
        "descriptions": {
            "weibo": "微博搜索爬虫",
            "douyin": "抖音搜索爬虫（开发中）",
        }
    }
