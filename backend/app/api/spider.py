"""Spider routes - Web scraping and data collection"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import os
import csv
import pandas as pd
from datetime import datetime
import random
import traceback

from ..database import get_db
from ..models.user import User
from ..core.deps import get_current_active_user
from ..schemas.spider import (
    SpiderTaskCreate,
    SpiderTaskHistory,
    SpiderTaskStatus,
    SpiderDataRecord,
    HotTopicItem
)
from ..services.spider_service import SpiderService
from ..utils.activity_logger import log_activity

router = APIRouter()
spider_service = SpiderService()


@router.post("/task", response_model=SpiderTaskStatus)
async def create_spider_task(
    task: SpiderTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建爬虫任务
    
    支持的平台：
    - weibo: 微博
    - douyin: 抖音
    - bilibili: B站
    """
    try:
        # 保存任务历史
        task_id = f"spider_{current_user.id}_{int(datetime.now().timestamp())}"
        
        # 启动爬虫任务
        result = await spider_service.execute_spider_task(
            keyword=task.keyword,
            platforms=task.platforms,
            start_date=task.start_date,
            end_date=task.end_date,
            precision=task.precision,
            user_id=current_user.id,
            task_id=task_id
        )
        
        # 记录活动日志
        log_activity(
            db,
            current_user,
            "spider_task",
            details=f"关键词: {task.keyword}, 平台: {', '.join(task.platforms)}"
        )
        
        # 如果有后台任务需求，添加到后台
        if result.get('background_task'):
            background_tasks.add_task(
                spider_service.process_spider_results,
                task_id,
                current_user.id
            )
        
        return SpiderTaskStatus(
            status="success",
            message="爬虫任务已启动",
            task_id=task_id,
            data=result.get('data')
        )
        
    except Exception as e:
        print(f"创建爬虫任务失败: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"爬虫任务失败: {str(e)}")


@router.get("/history", response_model=List[SpiderTaskHistory])
def get_spider_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
):
    """获取爬虫任务历史记录"""
    try:
        history = spider_service.get_task_history(current_user.id, limit)
        return history
    except Exception as e:
        print(f"获取历史记录失败: {str(e)}")
        return []


@router.get("/status/{task_id}", response_model=SpiderTaskStatus)
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """获取爬虫任务状态"""
    try:
        status = spider_service.get_task_status(task_id, current_user.id)
        return status
    except Exception as e:
        print(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/stop/{task_id}")
def stop_spider_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """停止爬虫任务"""
    try:
        spider_service.stop_task(task_id, current_user.id)
        return {"status": "success", "message": "任务已停止"}
    except Exception as e:
        print(f"停止任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止任务失败: {str(e)}")


@router.get("/hot-topics", response_model=List[HotTopicItem])
def get_hot_topics(
    platform: str = "douyin",
    current_user: User = Depends(get_current_active_user),
):
    """
    获取热点话题
    
    支持的平台：
    - douyin: 抖音热榜
    - weibo: 微博热搜
    - bilibili: B站热门
    """
    try:
        topics = spider_service.get_hot_topics(platform)
        return topics
    except Exception as e:
        print(f"获取热点话题失败: {str(e)}")
        return []


@router.get("/realtime-data")
def get_realtime_spider_data(
    task_id: str = None,
    current_user: User = Depends(get_current_active_user),
):
    """获取实时爬取数据"""
    try:
        if task_id:
            data = spider_service.get_realtime_data(task_id, current_user.id)
        else:
            # 获取最新的数据
            data = spider_service.get_latest_data(current_user.id)
        return data
    except Exception as e:
        print(f"获取实时数据失败: {str(e)}")
        return []


@router.get("/chart-data")
def get_spider_chart_data(
    task_id: str = None,
    current_user: User = Depends(get_current_active_user),
):
    """获取爬虫数据的图表统计信息"""
    try:
        chart_data = spider_service.get_chart_data(task_id, current_user.id)
        return chart_data
    except Exception as e:
        print(f"获取图表数据失败: {str(e)}")
        return {
            'heatmapData': [],
            'sentimentData': {'positive': 0, 'negative': 0, 'neutral': 0},
            'genderData': {'male': 0, 'female': 0}
        }
