"""
Schemas 包初始化
"""
from app.schemas.user import (
    UserBase, UserCreate, UserLogin, UserUpdate, UserPasswordUpdate, UserResponse,
    Token, TokenData
)
from app.schemas.task import (
    TaskType, TaskStatus, TaskBase, TaskCreate, TaskUpdate,
    TaskResponse, TaskListResponse
)
from app.schemas.data import (
    SentimentLabel, WeiboBase, WeiboCreate, WeiboResponse, WeiboListResponse,
    DouyinBase, DouyinCreate, DouyinResponse, DouyinListResponse
)
from app.schemas.common import (
    MessageResponse, ErrorResponse, PaginationParams, StatsResponse,
    SentimentDistribution, HomeDataResponse, WordCloudResponse,
    ReportRequest, ReportResponse, SentimentRequest, SentimentResult,
    SentimentResponse, PerformanceStats, CacheStats, AlertInfo, AlertListResponse
)
from app.schemas.system import (
    SystemConfigPayload,
    SystemConfigResponse,
    DesktopRuntimeResponse,
)

__all__ = [
    # User
    "UserBase", "UserCreate", "UserLogin", "UserUpdate", "UserPasswordUpdate", "UserResponse",
    "Token", "TokenData",
    # Task
    "TaskType", "TaskStatus", "TaskBase", "TaskCreate", "TaskUpdate",
    "TaskResponse", "TaskListResponse",
    # Data
    "SentimentLabel", "WeiboBase", "WeiboCreate", "WeiboResponse", "WeiboListResponse",
    "DouyinBase", "DouyinCreate", "DouyinResponse", "DouyinListResponse",
    # Common
    "MessageResponse", "ErrorResponse", "PaginationParams", "StatsResponse",
    "SentimentDistribution", "HomeDataResponse", "WordCloudResponse",
    "ReportRequest", "ReportResponse", "SentimentRequest", "SentimentResult",
    "SentimentResponse", "PerformanceStats", "CacheStats", "AlertInfo", "AlertListResponse",
    # System
    "SystemConfigPayload", "SystemConfigResponse", "DesktopRuntimeResponse",
]
