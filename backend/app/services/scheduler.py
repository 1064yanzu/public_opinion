"""
调度器核心服务
- 基于 asyncio 实现，与 FastAPI 异步模型完全兼容
- 时段感知动态间隔 (Smart Schedule)：根据舆情活跃规律自动调整爬取频率
- 调度配置持久化到 SQLite，应用重启后自动恢复
- 每个 Job 对应一个独立的 asyncio.Task，支持动态增删改
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.scheduled_job import ScheduledJob

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
#  时段感知间隔配置
#  格式: (start_hour, end_hour, interval_minutes, phase_label)
#  按 08:00~次日 08:00 的时段从高频到低频排列
# ─────────────────────────────────────────────────────────
SMART_SCHEDULE_PHASES = [
    (6,  9,  15, "早间高峰",   "🌅"),   # 06:00-09:00  舆情爆发高峰
    (9,  12, 20, "上午活跃",   "☀️"),   # 09:00-12:00  工作时段活跃
    (12, 14, 35, "午间平稳",   "🌤"),   # 12:00-14:00  午休时段
    (14, 18, 20, "下午活跃",   "⛅️"),   # 14:00-18:00  下午工作
    (18, 21, 15, "晚间高峰",   "🌆"),   # 18:00-21:00  热搜爆发高峰
    (21, 23, 60, "夜间收尾",   "🌙"),   # 21:00-23:00  舆情降温
    (23, 24, 120, "深夜安静",  "🌛"),   # 23:00-00:00  深夜
    (0,  6,  120, "深夜安静",  "🌛"),   # 00:00-06:00  凌晨
]


def get_smart_interval(now: datetime) -> Tuple[int, str, str]:
    """
    根据当前北京时间(CST)计算应使用的爬取间隔。

    Returns:
        (interval_minutes, phase_label, emoji)
    """
    # 统一转换为北京时间 (UTC+8)
    if now.tzinfo is None:
        cst = now
    else:
        cst = now.astimezone(timezone(timedelta(hours=8)))
    hour = cst.hour

    for start, end, minutes, label, emoji in SMART_SCHEDULE_PHASES:
        if start <= hour < end:
            return minutes, label, emoji

    # 兜底（不应触达）
    return 30, "标准", "⏱"


def describe_smart_schedule() -> list[dict]:
    """返回全天时段配置供前端展示。"""
    return [
        {
            "start": f"{start:02d}:00",
            "end":   f"{end:02d}:00" if end != 24 else "24:00",
            "interval_minutes": minutes,
            "label": label,
            "emoji": emoji,
        }
        for start, end, minutes, label, emoji in SMART_SCHEDULE_PHASES
    ]


class SchedulerService:
    """
    全局单例调度器。
    维护一个 in-memory 的 {job_id: asyncio.Task} 字典，
    启动时从数据库恢复所有 is_active=True 的任务。
    """

    _instance: Optional["SchedulerService"] = None

    def __init__(self):
        self._tasks: Dict[int, asyncio.Task] = {}
        self._running = False

    @classmethod
    def get_instance(cls) -> "SchedulerService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── 生命周期 ────────────────────────────────────────
    async def start(self):
        self._running = True
        logger.info("调度器启动中，正在恢复定时任务...")
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ScheduledJob).where(ScheduledJob.is_active == True)  # noqa: E712
            )
            jobs = result.scalars().all()

        for job in jobs:
            await self._spawn_task(
                job.id, job.keyword, job.task_type,
                job.max_page, job.interval_minutes,
                job.use_smart_schedule, job.next_run_at,
            )
        logger.info("调度器启动完成，已恢复 %d 个定时任务", len(jobs))

    async def stop(self):
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()
        logger.info("调度器已关闭")

    # ── 公开 API ────────────────────────────────────────
    async def add_job(
        self,
        db: AsyncSession,
        keyword: str,
        task_type: str,
        max_page: int,
        interval_minutes: int,
        use_smart_schedule: bool = True,
    ) -> ScheduledJob:
        now = datetime.now(timezone.utc)
        job = ScheduledJob(
            keyword=keyword,
            task_type=task_type,
            max_page=max_page,
            interval_minutes=interval_minutes,
            use_smart_schedule=use_smart_schedule,
            is_active=True,
            next_run_at=now,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        await self._spawn_task(
            job.id, keyword, task_type,
            max_page, interval_minutes,
            use_smart_schedule, now,
        )
        logger.info("定时任务已创建: job_id=%d keyword=%s smart=%s", job.id, keyword, use_smart_schedule)
        return job

    async def remove_job(self, db: AsyncSession, job_id: int):
        await self._cancel_task(job_id)
        result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            await db.delete(job)
            await db.commit()

    async def toggle_job(self, db: AsyncSession, job_id: int, is_active: bool) -> ScheduledJob:
        result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"定时任务 {job_id} 不存在")

        job.is_active = is_active
        if is_active:
            job.next_run_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(job)

        if is_active:
            await self._spawn_task(
                job.id, job.keyword, job.task_type,
                job.max_page, job.interval_minutes,
                job.use_smart_schedule, job.next_run_at,
            )
        else:
            await self._cancel_task(job_id)
        return job

    async def update_job(
        self,
        db: AsyncSession,
        job_id: int,
        interval_minutes: Optional[int] = None,
        max_page: Optional[int] = None,
        use_smart_schedule: Optional[bool] = None,
    ) -> ScheduledJob:
        result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"定时任务 {job_id} 不存在")

        if interval_minutes is not None:
            job.interval_minutes = interval_minutes
        if max_page is not None:
            job.max_page = max_page
        if use_smart_schedule is not None:
            job.use_smart_schedule = use_smart_schedule
        job.next_run_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(job)

        if job.is_active:
            await self._cancel_task(job_id)
            await self._spawn_task(
                job.id, job.keyword, job.task_type,
                job.max_page, job.interval_minutes,
                job.use_smart_schedule, job.next_run_at,
            )
        return job

    def get_active_count(self) -> int:
        return len([t for t in self._tasks.values() if not t.done()])

    def is_running(self) -> bool:
        return self._running

    # ── 内部实现 ─────────────────────────────────────────
    async def _spawn_task(
        self,
        job_id: int,
        keyword: str,
        task_type: str,
        max_page: int,
        interval_minutes: int,
        use_smart_schedule: bool,
        first_run_at: Optional[datetime],
    ):
        await self._cancel_task(job_id)
        task = asyncio.create_task(
            self._job_loop(
                job_id, keyword, task_type, max_page,
                interval_minutes, use_smart_schedule, first_run_at,
            ),
            name=f"scheduled_job_{job_id}",
        )
        self._tasks[job_id] = task
        task.add_done_callback(lambda t: self._tasks.pop(job_id, None))

    async def _cancel_task(self, job_id: int):
        task = self._tasks.pop(job_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    async def _job_loop(
        self,
        job_id: int,
        keyword: str,
        task_type: str,
        max_page: int,
        interval_minutes: int,
        use_smart_schedule: bool,
        first_run_at: Optional[datetime],
    ):
        """
        定时任务主循环：
        1. 等待到 first_run_at（或立即执行）
        2. 执行一次爬虫
        3. 根据当前时段（智能模式）或固定值计算下次等待时间
        4. 更新数据库中的 next_run_at
        5. 重复 2-4
        """
        # 首次执行等待
        if first_run_at:
            now_utc = datetime.now(timezone.utc)
            if first_run_at.tzinfo is None:
                first_run_at = first_run_at.replace(tzinfo=timezone.utc)
            delay = (first_run_at - now_utc).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)

        logger.info("定时任务 job_id=%d 开始运行 keyword=%s smart=%s", job_id, keyword, use_smart_schedule)

        while True:
            try:
                await self._execute_once(job_id, keyword, task_type, max_page)
            except asyncio.CancelledError:
                logger.info("定时任务 job_id=%d 已取消", job_id)
                raise
            except Exception as e:
                logger.error("定时任务 job_id=%d 执行异常: %s", job_id, e, exc_info=True)
                await self._record_error(job_id, str(e))

            # 计算下次间隔
            now = datetime.now(timezone.utc)
            if use_smart_schedule:
                sleep_minutes, phase, emoji = get_smart_interval(now)
                logger.info(
                    "定时任务 job_id=%d 当前时段: %s %s，下次采集 %d 分钟后",
                    job_id, emoji, phase, sleep_minutes,
                )
            else:
                sleep_minutes = interval_minutes
                logger.info("定时任务 job_id=%d 固定间隔 %d 分钟", job_id, sleep_minutes)

            next_run = now + timedelta(minutes=sleep_minutes)
            await self._update_next_run(job_id, next_run)
            await asyncio.sleep(sleep_minutes * 60)

    async def _execute_once(self, job_id: int, keyword: str, task_type: str, max_page: int):
        """执行一次采集并更新数据库状态。"""
        from app.models.task import Task
        from app.routers.spider import execute_spider_task

        now = datetime.now(timezone.utc)
        created_task_id = None

        async with AsyncSessionLocal() as db:
            spider_task = Task(
                task_type=task_type,
                keyword=keyword,
                max_page=max_page,
                status="processing",
                started_at=now,
                config={"source": "scheduled", "scheduled_job_id": job_id},
            )
            db.add(spider_task)
            await db.commit()
            await db.refresh(spider_task)
            created_task_id = spider_task.id

            try:
                count = await execute_spider_task(task_type, keyword, max_page, spider_task, db)
                spider_task.status = "completed"
                spider_task.progress = 100
                spider_task.completed_at = datetime.now(timezone.utc)
                await db.commit()
                logger.info("定时任务 job_id=%d 采集完成，共 %d 条", job_id, count)
            except Exception as e:
                await db.rollback()
                result = await db.execute(select(Task).where(Task.id == created_task_id))
                _task = result.scalar_one_or_none()
                if _task:
                    _task.status = "failed"
                    _task.error_message = str(e)[:500]
                    await db.commit()
                raise

        # 更新 ScheduledJob 统计
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.last_run_at = now
                job.run_count = (job.run_count or 0) + 1
                job.last_error = None
                job.last_task_id = created_task_id
                await db.commit()

    async def _update_next_run(self, job_id: int, next_run: datetime):
        """写入下次执行时间（用于前端展示倒计时）。"""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
                job = result.scalar_one_or_none()
                if job:
                    job.next_run_at = next_run
                    await db.commit()
        except Exception as e:
            logger.error("更新 next_run_at 失败: %s", e)

    async def _record_error(self, job_id: int, error_msg: str):
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(ScheduledJob).where(ScheduledJob.id == job_id))
                job = result.scalar_one_or_none()
                if job:
                    job.last_error = error_msg[:500]
                    await db.commit()
        except Exception as e:
            logger.error("记录错误时失败: %s", e)


# 全局单例
scheduler_service = SchedulerService.get_instance()
