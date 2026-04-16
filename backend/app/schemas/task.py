"""
任务相关 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class TaskType(str, Enum):
    """任务类型枚举"""
    WEIBO = "weibo"
    DOUYIN = "douyin"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskBase(BaseModel):
    """任务基础模型"""
    task_type: TaskType = Field(..., description="任务类型：weibo/douyin")
    keyword: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    max_page: int = Field(default=10, ge=1, le=50, description="最大爬取页数")


class TaskCreate(TaskBase):
    """创建任务请求"""
    async_mode: bool = Field(default=False, description="是否异步执行")
    config: Optional[Dict[str, Any]] = Field(None, description="额外配置参数")


class TaskUpdate(BaseModel):
    """更新任务状态"""
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")
    error_message: Optional[str] = Field(None, description="错误信息")


class TaskResponse(TaskBase):
    """任务响应"""
    id: int = Field(..., description="任务ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int = Field(..., description="总数")
    tasks: List[TaskResponse] = Field(..., description="任务列表")
