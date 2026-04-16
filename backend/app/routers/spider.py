"""
爬虫相关 API 路由
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.dependencies import get_db, get_current_user, get_current_user_optional
from app.models.user import User
from app.models.task import Task
from app.models.weibo import WeiboData
from app.models.douyin import DouyinData
from app.schemas import (
    TaskCreate, TaskResponse, TaskListResponse, TaskStatus, TaskType,
    WeiboListResponse, WeiboResponse, DouyinListResponse, DouyinResponse,
    MessageResponse
)

router = APIRouter()


# ===== 爬虫任务 =====
@router.post("/search", response_model=TaskResponse, summary="创建搜索任务", 
             description="创建微博或抖音搜索爬虫任务")
async def create_search_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    创建搜索爬虫任务
    
    - **task_type**: 任务类型（weibo/douyin）
    - **keyword**: 搜索关键词
    - **max_page**: 最大爬取页数（1-50）
    - **async_mode**: 是否异步执行（后台运行）
    """
    # 创建任务记录
    task = Task(
        user_id=current_user.id if current_user else None,
        task_type=task_data.task_type.value,
        keyword=task_data.keyword.strip(),
        max_page=task_data.max_page,
        status="pending",
        config=task_data.config,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    if task_data.async_mode:
        # 异步执行：添加后台任务
        background_tasks.add_task(
            execute_spider_task_async, 
            task.id, 
            task_data.task_type.value, 
            task_data.keyword, 
            task_data.max_page
        )
        task.status = "processing"
        task.started_at = datetime.utcnow()
        await db.commit()
        await db.refresh(task)
    else:
        # 同步执行
        try:
            task.status = "processing"
            task.started_at = datetime.utcnow()
            await db.commit()
            
            # 执行爬虫
            count = await execute_spider_task(
                task_data.task_type.value,
                task_data.keyword,
                task_data.max_page,
                task,
                db
            )
            
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(task)
            
        except Exception as e:
            await db.rollback()
            result = await db.execute(select(Task).where(Task.id == task.id))
            _task = result.scalar_one_or_none()
            if _task:
                _task.status = "failed"
                _task.error_message = str(e)[:500]
                await db.commit()
            raise HTTPException(status_code=500, detail=f"爬虫执行失败: {str(e)}")
    
    return task


async def execute_spider_task(
    task_type: str, 
    keyword: str, 
    max_page: int,
    task: Task,
    db: AsyncSession
) -> int:
    """执行爬虫任务"""
    if task_type == "weibo":
        from app.services.weibo_spider import WeiboSpider
        spider = WeiboSpider()
        return await spider.search_and_save(keyword, max_page, task, db)
    elif task_type == "douyin":
        from app.services.douyin_spider import DouyinSpider
        spider = DouyinSpider()
        return await spider.search_and_save(keyword, max_page, task, db)
    else:
        raise ValueError(f"不支持的任务类型: {task_type}")


async def execute_spider_task_async(task_id: int, task_type: str, keyword: str, max_page: int):
    """后台执行爬虫任务"""
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取任务
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            
            if not task:
                print(f"任务 {task_id} 不存在")
                return
            
            # 执行爬虫
            count = await execute_spider_task(task_type, keyword, max_page, task, db)
            
            # 更新状态
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            await db.commit()
            
            print(f"任务 {task_id} 完成，共获取 {count} 条数据")
            
        except Exception as e:
            print(f"任务 {task_id} 失败: {e}")
            await db.rollback()
            result = await db.execute(select(Task).where(Task.id == task_id))
            _task = result.scalar_one_or_none()
            if _task:
                _task.status = "failed"
                _task.error_message = str(e)[:500]
                await db.commit()


@router.get("/tasks", response_model=TaskListResponse, summary="获取任务列表",
            description="获取当前用户的爬虫任务列表")
async def get_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取爬虫任务列表"""
    query = select(Task)
    
    if current_user:
        query = query.where(Task.user_id == current_user.id)
    
    if status:
        query = query.where(Task.status == status.value)
    
    # 统计总数
    count_query = select(func.count()).select_from(Task)
    if current_user:
        count_query = count_query.where(Task.user_id == current_user.id)
    if status:
        count_query = count_query.where(Task.status == status.value)
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页查询
    query = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return TaskListResponse(total=total, tasks=tasks)


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="获取任务详情",
            description="获取指定任务的详细信息")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务详情"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task


@router.post("/tasks/{task_id}/cancel", response_model=MessageResponse, summary="取消任务",
             description="取消正在执行的任务")
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.user_id and task.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    if task.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="任务已完成或已取消")
    
    task.status = "cancelled"
    task.completed_at = datetime.utcnow()
    await db.commit()
    
    return MessageResponse(message="任务已取消", success=True)


@router.delete("/tasks/{task_id}", response_model=MessageResponse, summary="删除任务",
               description="删除任务记录及关联的采集数据")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """删除任务及其所有关联数据"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await db.delete(task)
    await db.commit()

    return MessageResponse(message="任务已删除", success=True)


# ===== 数据查询 =====
@router.get("/weibo", response_model=WeiboListResponse, summary="获取微博数据",
            description="获取微博爬虫数据列表")
async def get_weibo_data(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="内容关键词搜索"),
    sentiment: Optional[str] = Query(None, description="情感筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取微博数据列表"""
    query = select(WeiboData)
    count_query = select(func.count()).select_from(WeiboData)
    
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
        count_query = count_query.where(WeiboData.task_id == task_id)
    
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
        count_query = count_query.where(WeiboData.content.contains(keyword))
    
    if sentiment:
        query = query.where(WeiboData.sentiment_label == sentiment)
        count_query = count_query.where(WeiboData.sentiment_label == sentiment)
    
    # 统计总数
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页查询
    query = query.order_by(WeiboData.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    data = result.scalars().all()
    
    return WeiboListResponse(total=total, data=data)


@router.get("/douyin", response_model=DouyinListResponse, summary="获取抖音数据",
            description="获取抖音爬虫数据列表")
async def get_douyin_data(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="内容关键词搜索"),
    sentiment: Optional[str] = Query(None, description="情感筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取抖音数据列表"""
    query = select(DouyinData)
    count_query = select(func.count()).select_from(DouyinData)
    
    if task_id:
        query = query.where(DouyinData.task_id == task_id)
        count_query = count_query.where(DouyinData.task_id == task_id)
    
    if keyword:
        query = query.where(DouyinData.content.contains(keyword))
        count_query = count_query.where(DouyinData.content.contains(keyword))
    
    if sentiment:
        query = query.where(DouyinData.sentiment_label == sentiment)
        count_query = count_query.where(DouyinData.sentiment_label == sentiment)
    
    # 统计总数
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页查询
    query = query.order_by(DouyinData.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    data = result.scalars().all()
    
    return DouyinListResponse(total=total, data=data)
