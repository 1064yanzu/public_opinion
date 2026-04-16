"""
定时采集任务相关 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ScheduledJobCreate(BaseModel):
    """创建定时采集任务"""
    keyword: str = Field(..., min_length=1, max_length=200, description="监控关键词")
    task_type: str = Field(default="weibo", description="平台：weibo / douyin")
    max_page: int = Field(default=5, ge=1, le=50, description="每次采集页数")
    use_smart_schedule: bool = Field(default=True, description="是否使用时段感知智能间隔")
    # 仅 use_smart_schedule=False 时生效
    interval_minutes: int = Field(default=30, ge=5, le=1440, description="手动采集间隔（分钟）")


class ScheduledJobUpdate(BaseModel):
    """更新定时采集任务"""
    interval_minutes: Optional[int] = Field(None, ge=5, le=1440, description="手动采集间隔（分钟）")
    max_page: Optional[int] = Field(None, ge=1, le=50, description="每次采集页数")
    is_active: Optional[bool] = Field(None, description="是否启用")
    use_smart_schedule: Optional[bool] = Field(None, description="是否使用智能间隔")


class ScheduledJobResponse(BaseModel):
    """定时采集任务响应"""
    id: int
    keyword: str
    task_type: str
    max_page: int
    interval_minutes: int
    use_smart_schedule: bool = True
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    last_error: Optional[str] = None
    last_task_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduledJobListResponse(BaseModel):
    """定时采集任务列表响应"""
    total: int
    jobs: List[ScheduledJobResponse]


class SmartPhaseInfo(BaseModel):
    """单个时段配置"""
    start: str      # "06:00"
    end: str        # "09:00"
    interval_minutes: int
    label: str      # "早间高峰"
    emoji: str      # "🌅"


class SchedulerStatusResponse(BaseModel):
    """调度器全局状态"""
    is_running: bool = Field(..., description="调度器是否运行中")
    active_jobs: int = Field(..., description="活跃定时任务数")
    total_jobs: int = Field(..., description="总定时任务数")
    message: str = Field(..., description="状态描述")
    current_phase: Optional[str] = Field(None, description="当前时段名称")
    current_phase_emoji: Optional[str] = Field(None, description="当前时段图标")
    current_interval: Optional[int] = Field(None, description="当前智能间隔（分钟）")
    smart_phases: Optional[List[SmartPhaseInfo]] = Field(None, description="全天时段配置")
