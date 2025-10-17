"""Wordcloud API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from ..database import get_db
from ..models.dataset import DataSet
from ..models.record import DataRecord
from ..models.user import User
from ..core.deps import get_current_active_user
from ..services.wordcloud_service import WordCloudService

router = APIRouter()


class WordCloudRequest(BaseModel):
    """Wordcloud request schema"""
    dataset_id: int
    max_words: int = Field(200, ge=10, le=500)
    colormap: str = Field("viridis", max_length=50)
    width: int = Field(800, ge=100, le=1600)
    height: int = Field(600, ge=100, le=1200)
    mask_image: Optional[str] = None


@router.post("/generate")
def generate_wordcloud(
    request: WordCloudRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate wordcloud for dataset records
    
    Returns base64 image and word frequencies
    """
    dataset = db.query(DataSet).filter(
        DataSet.id == request.dataset_id,
        DataSet.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    records = (
        db.query(DataRecord)
        .filter(DataRecord.dataset_id == request.dataset_id)
        .order_by(DataRecord.created_at.asc())
        .all()
    )
    
    if not records:
        raise HTTPException(status_code=400, detail="Dataset has no records")
    
    wc_service = WordCloudService(stopwords_path="stopwords.txt")
    
    try:
        mask_image = dataset.file_path if request.mask_image == "dataset" else request.mask_image
        result = wc_service.generate_from_records(
            records,
            content_field='content',
            mask_image_path=mask_image,
            width=request.width,
            height=request.height,
            max_words=request.max_words,
            colormap=request.colormap,
        )
        
        return {
            "image_base64": result['image_base64'],
            "word_frequencies": result['word_frequencies'],
            "total_words": result['total_words'],
            "unique_words": result['unique_words'],
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wordcloud generation failed: {str(e)}")
