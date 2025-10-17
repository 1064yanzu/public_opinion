"""Report generation routes - AI-powered sentiment report generation"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
from typing import AsyncGenerator

from ..database import get_db
from ..models.user import User
from ..models.dataset import DataSet
from ..core.deps import get_current_active_user
from ..schemas.report import ReportGenerateRequest, ReportSection
from ..services.report_service import ReportService
from ..utils.activity_logger import log_activity

router = APIRouter()


@router.post("/generate")
async def generate_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    生成舆情分析报告（流式输出）
    
    支持的深度级别：
    - simple: 简单报告
    - standard: 标准报告  
    - detailed: 详细报告
    
    报告包含：
    - 舆情概述
    - 数据分析
    - 应对建议
    - 风险提示
    """
    try:
        # 验证dataset是否存在且属于当前用户
        if request.dataset_id:
            dataset = db.query(DataSet).filter(
                DataSet.id == request.dataset_id,
                DataSet.user_id == current_user.id
            ).first()
            if not dataset:
                raise HTTPException(status_code=404, detail="数据集不存在")
        
        # 初始化报告服务
        report_service = ReportService(db)
        
        # 生成报告流
        async def generate_stream() -> AsyncGenerator[str, None]:
            try:
                async for chunk in report_service.generate_report_stream(
                    dataset_id=request.dataset_id,
                    depth=request.depth,
                    include_sections=request.include_sections,
                    user_id=current_user.id
                ):
                    yield json.dumps(chunk, ensure_ascii=False) + "\n"
            except Exception as e:
                yield json.dumps({"error": str(e)}, ensure_ascii=False) + "\n"
        
        # 记录活动
        log_activity(
            db,
            current_user,
            "generate_report",
            resource="dataset",
            resource_id=request.dataset_id,
            details=f"深度: {request.depth}"
        )
        
        return StreamingResponse(
            generate_stream(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@router.get("/history")
def get_report_history(
    dataset_id: int = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取报告生成历史"""
    # TODO: 实现报告历史记录功能
    return []


@router.post("/export/{report_id}")
def export_report(
    report_id: int,
    format: str = "pdf",  # pdf, word, html
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """导出报告为文件"""
    # TODO: 实现报告导出功能
    raise HTTPException(status_code=501, detail="功能开发中")
