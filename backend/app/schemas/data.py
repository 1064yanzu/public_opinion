"""
微博数据相关 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SentimentLabel(str, Enum):
    """情感标签枚举"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class WeiboBase(BaseModel):
    """微博数据基础模型"""
    weibo_id: str = Field(..., description="微博ID")
    content: Optional[str] = Field(None, description="微博内容")
    user_name: Optional[str] = Field(None, description="用户昵称")
    user_id: Optional[str] = Field(None, description="用户ID")
    publish_time: Optional[datetime] = Field(None, description="发布时间")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="转发数")
    url: Optional[str] = Field(None, description="链接")


class WeiboCreate(WeiboBase):
    """创建微博数据"""
    task_id: Optional[int] = Field(None, description="关联任务ID")


class WeiboResponse(WeiboBase):
    """微博数据响应"""
    id: int = Field(..., description="数据ID")
    task_id: Optional[int] = Field(None, description="关联任务ID")
    sentiment_score: Optional[float] = Field(None, ge=0, le=1, description="情感分数")
    sentiment_label: Optional[SentimentLabel] = Field(None, description="情感标签")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class WeiboListResponse(BaseModel):
    """微博数据列表响应"""
    total: int = Field(..., description="总数")
    data: List[WeiboResponse] = Field(..., description="数据列表")


class DouyinBase(BaseModel):
    """抖音数据基础模型"""
    video_id: str = Field(..., description="视频ID")
    title: Optional[str] = Field(None, description="视频标题")
    content: Optional[str] = Field(None, description="视频描述")
    author: Optional[str] = Field(None, description="作者昵称")
    author_id: Optional[str] = Field(None, description="作者ID")
    publish_time: Optional[datetime] = Field(None, description="发布时间")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="分享数")
    url: Optional[str] = Field(None, description="链接")


class DouyinCreate(DouyinBase):
    """创建抖音数据"""
    task_id: Optional[int] = Field(None, description="关联任务ID")


class DouyinResponse(DouyinBase):
    """抖音数据响应"""
    id: int = Field(..., description="数据ID")
    task_id: Optional[int] = Field(None, description="关联任务ID")
    sentiment_score: Optional[float] = Field(None, ge=0, le=1, description="情感分数")
    sentiment_label: Optional[SentimentLabel] = Field(None, description="情感标签")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class DouyinListResponse(BaseModel):
    """抖音数据列表响应"""
    total: int = Field(..., description="总数")
    data: List[DouyinResponse] = Field(..., description="数据列表")
