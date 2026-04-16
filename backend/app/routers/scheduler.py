"""
定时采集任务 API 路由
"""
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user_optional
from app.models.user import User
from app.models.scheduled_job import ScheduledJob
from app.schemas.scheduler import (
    ScheduledJobCreate,
    ScheduledJobUpdate,
    ScheduledJobResponse,
    ScheduledJobListResponse,
    SchedulerStatusResponse,
    SmartPhaseInfo,
)
from app.services.scheduler import scheduler_service, get_smart_interval, describe_smart_schedule

router = APIRouter()


@router.get("/status", response_model=SchedulerStatusResponse, summary="调度器全局状态")
async def get_scheduler_status(db: AsyncSession = Depends(get_db)):
    """获取调度器运行状态、当前时段信息及全天配置。"""
    total_result = await db.execute(select(func.count()).select_from(ScheduledJob))
    total = total_result.scalar() or 0

    active_running = scheduler_service.get_active_count()

    now = datetime.now(timezone.utc)
    current_interval, current_phase, current_emoji = get_smart_interval(now)
    phases = [SmartPhaseInfo(**p) for p in describe_smart_schedule()]

    return SchedulerStatusResponse(
        is_running=scheduler_service.is_running(),
        active_jobs=active_running,
        total_jobs=total,
        message=(
            f"调度器运行中 · {current_emoji} {current_phase}"
            if scheduler_service.is_running()
            else "调度器未启动"
        ),
        current_phase=current_phase,
        current_phase_emoji=current_emoji,
        current_interval=current_interval,
        smart_phases=phases,
    )


@router.get("/jobs", response_model=ScheduledJobListResponse, summary="定时任务列表")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None, description="筛选启用状态"),
    db: AsyncSession = Depends(get_db),
):
    query = select(ScheduledJob)
    count_query = select(func.count()).select_from(ScheduledJob)

    if is_active is not None:
        query = query.where(ScheduledJob.is_active == is_active)
        count_query = count_query.where(ScheduledJob.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        query.order_by(ScheduledJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    jobs = result.scalars().all()

    return ScheduledJobListResponse(total=total, jobs=list(jobs))


@router.get("/jobs/{job_id}", response_model=ScheduledJobResponse, summary="定时任务详情")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    return job


@router.post("/jobs", response_model=ScheduledJobResponse, summary="创建定时任务")
async def create_job(
    payload: ScheduledJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    创建定时采集任务。

    - 默认开启 **智能间隔**（use_smart_schedule=true）：系统自动根据时段调整频率，无需手动设置。
    - 若 use_smart_schedule=false 则使用 interval_minutes 固定值。
    - 创建后**立即执行第一次采集**。
    """
    job = await scheduler_service.add_job(
        db=db,
        keyword=payload.keyword.strip(),
        task_type=payload.task_type,
        max_page=payload.max_page,
        interval_minutes=payload.interval_minutes,
        use_smart_schedule=payload.use_smart_schedule,
    )
    return job


@router.patch("/jobs/{job_id}", response_model=ScheduledJobResponse, summary="更新定时任务")
async def update_job(
    job_id: int,
    payload: ScheduledJobUpdate,
    db: AsyncSession = Depends(get_db),
):
    """动态更新定时任务参数，修改后立即重启对应 asyncio Task 生效。"""
    result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    try:
        # 启停操作
        if payload.is_active is not None:
            job = await scheduler_service.toggle_job(db, job_id, payload.is_active)

        # 参数更新（包括 is_active 后新的 is_active 状态）
        has_param_update = any([
            payload.interval_minutes is not None,
            payload.max_page is not None,
            payload.use_smart_schedule is not None,
        ])
        if has_param_update:
            job = await scheduler_service.update_job(
                db, job_id,
                interval_minutes=payload.interval_minutes,
                max_page=payload.max_page,
                use_smart_schedule=payload.use_smart_schedule,
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return job


@router.delete("/jobs/{job_id}", summary="删除定时任务")
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """删除定时任务（同时停止后台循环）。"""
    result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    await scheduler_service.remove_job(db, job_id)
    return {"success": True, "message": f"定时任务 {job_id} 已删除"}


@router.post("/jobs/{job_id}/trigger", response_model=ScheduledJobResponse, summary="立即触发一次采集")
async def trigger_job_now(job_id: int, db: AsyncSession = Depends(get_db)):
    """
    不等待间隔，立即触发该任务执行一次采集。
    触发后定时任务的常规循环**不受影响**，仍按时段调度。
    """
    result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    import asyncio
    asyncio.create_task(
        scheduler_service._execute_once(job_id, job.keyword, job.task_type, job.max_page)
    )
    return job
