"""
定时采集任务数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.database import Base


class ScheduledJob(Base):
    """定时采集任务表 — 持久化调度配置，应用重启后自动恢复"""
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 基本配置
    keyword = Column(String(200), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, default="weibo")   # 'weibo' | 'douyin'
    max_page = Column(Integer, default=5, nullable=False)
    # 调度配置
    interval_minutes = Column(Integer, nullable=False, default=30)    # 手动间隔（仅 use_smart_schedule=False 时生效）
    use_smart_schedule = Column(Boolean, default=True, nullable=False) # 是否使用时段感知动态间隔
    is_active = Column(Boolean, default=True, nullable=False)         # 是否启用
    # 运行状态
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    run_count = Column(Integer, default=0, nullable=False)            # 累计执行次数
    last_error = Column(Text, nullable=True)
    last_task_id = Column(Integer, nullable=True)                     # 最近一次生成的 Task ID
    # 额外配置
    config = Column(JSON, nullable=True)
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<ScheduledJob(id={self.id}, keyword='{self.keyword}', "
            f"interval={self.interval_minutes}m, active={self.is_active})>"
        )
