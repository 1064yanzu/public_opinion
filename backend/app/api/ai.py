"""AI Assistant API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from ..database import get_db
from ..models.user import User
from ..models.dataset import DataSet
from ..core.deps import get_current_active_user
from ..services.ai_service import AIService
from ..services.analytics_service import AnalyticsService
import json

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message schema"""
    role: str  # system, user, assistant
    content: str


class ChatRequest(BaseModel):
    """Chat request schema"""
    messages: List[ChatMessage]
    provider: Optional[str] = None
    stream: bool = True


class ReportRequest(BaseModel):
    """Report generation request"""
    dataset_id: int
    sections: Optional[List[str]] = None
    provider: Optional[str] = None


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Chat with AI assistant
    
    Can be used for general questions or analysis assistance
    """
    ai_service = AIService()
    
    messages = [msg.dict() for msg in request.messages]
    
    try:
        if request.stream:
            def generate():
                response = ai_service.chat(
                    messages,
                    provider=request.provider,
                    stream=True
                )
                
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content'):
                        content = chunk.choices[0].delta.content
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"
                
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            response = ai_service.chat(
                messages,
                provider=request.provider,
                stream=False
            )
            return {
                "content": response.choices[0].message.content,
                "usage": response.usage.dict() if hasattr(response, 'usage') else None
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/report")
def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate AI analysis report for a dataset
    
    Streams markdown-formatted report sections
    """
    # Verify dataset access
    dataset = db.query(DataSet).filter(
        DataSet.id == request.dataset_id,
        DataSet.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get analytics context
    analytics_service = AnalyticsService(db)
    summary = analytics_service.dataset_summary(request.dataset_id, current_user.id)
    
    # Build analysis context for AI
    analysis_context = {
        'dataset_name': dataset.name,
        'dataset_description': dataset.description,
        'source': dataset.source.value,
        'keyword': dataset.keyword,
        'total_records': summary.total_records,
        'sentiment': {
            'positive': summary.sentiment.positive,
            'negative': summary.sentiment.negative,
            'neutral': summary.sentiment.neutral,
            'total': summary.sentiment.total,
            'positive_pct': (summary.sentiment.positive / summary.sentiment.total * 100) if summary.sentiment.total > 0 else 0,
            'negative_pct': (summary.sentiment.negative / summary.sentiment.total * 100) if summary.sentiment.total > 0 else 0,
            'neutral_pct': (summary.sentiment.neutral / summary.sentiment.total * 100) if summary.sentiment.total > 0 else 0,
        },
        'keywords': [item['keyword'] for item in summary.top_keywords],
        'avg_sentiment': summary.avg_sentiment,
        'total_likes': summary.total_likes,
        'total_shares': summary.total_shares,
        'total_comments': summary.total_comments,
    }
    
    # Generate report
    ai_service = AIService()
    
    def generate():
        try:
            for chunk in ai_service.generate_report(
                analysis_context,
                sections=request.sections,
                provider=request.provider
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_chunk = {
                'type': 'error',
                'content': f'生成报告时出错: {str(e)}'
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/providers")
def list_providers(
    current_user: User = Depends(get_current_active_user),
):
    """List available AI providers"""
    ai_service = AIService()
    available = ai_service.available_providers()
    
    return {
        "available": available,
        "descriptions": {
            "siliconflow": "SiliconFlow Cloud AI",
            "zhipuai": "智谱AI GLM系列",
        }
    }
