"""
通用响应 Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str = Field(..., description="消息内容")
    success: bool = Field(default=True, description="是否成功")


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str = Field(..., description="错误详情")
    error_code: Optional[str] = Field(None, description="错误码")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class StatsResponse(BaseModel):
    """统计数据响应"""
    total_count: int = Field(..., description="总数据量")
    today_count: int = Field(default=0, description="今日新增")
    positive_count: int = Field(default=0, description="正面数据量")
    negative_count: int = Field(default=0, description="负面数据量")
    neutral_count: int = Field(default=0, description="中性数据量")


class SentimentDistribution(BaseModel):
    """情感分布"""
    positive: float = Field(..., ge=0, le=100, description="正面占比")
    negative: float = Field(..., ge=0, le=100, description="负面占比")
    neutral: float = Field(..., ge=0, le=100, description="中性占比")


class HomeDataResponse(BaseModel):
    """主页数据响应"""
    stats: StatsResponse = Field(..., description="统计数据")
    sentiment_distribution: SentimentDistribution = Field(..., description="情感分布")
    recent_data: List[Dict[str, Any]] = Field(default=[], description="最近数据")
    hotspots: List[Dict[str, Any]] = Field(default=[], description="热点数据")


class WordCloudResponse(BaseModel):
    """词云响应"""
    image_url: str = Field(..., description="词云图片URL")
    word_freq: Dict[str, int] = Field(default={}, description="词频统计")


class ReportRequest(BaseModel):
    """报告生成请求"""
    keyword: str = Field(..., description="分析关键词")
    report_type: str = Field(default="comprehensive", description="报告类型")


class ReportResponse(BaseModel):
    """报告响应"""
    report_id: str = Field(..., description="报告ID")
    status: str = Field(..., description="状态")
    download_url: Optional[str] = Field(None, description="下载链接")
    content: Optional[Dict[str, Any]] = Field(None, description="报告内容")


class SentimentRequest(BaseModel):
    """情感分析请求"""
    texts: List[str] = Field(..., min_length=1, description="待分析文本列表")


class SentimentResult(BaseModel):
    """情感分析结果"""
    text: str = Field(..., description="原文本")
    sentiment: str = Field(..., description="情感标签")
    score: float = Field(..., ge=0, le=1, description="情感分数")


class SentimentResponse(BaseModel):
    """情感分析响应"""
    results: List[SentimentResult] = Field(..., description="分析结果")


class PerformanceStats(BaseModel):
    """性能统计"""
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    uptime: int = Field(..., description="运行时间（秒）")


class CacheStats(BaseModel):
    """缓存统计"""
    total_size: int = Field(..., description="总大小（字节）")
    item_count: int = Field(..., description="缓存项数量")
    hit_rate: float = Field(..., description="命中率")


class AlertInfo(BaseModel):
    """告警信息"""
    id: str = Field(..., description="告警ID")
    level: str = Field(..., description="告警级别")
    type: str = Field(..., description="告警类型")
    message: str = Field(..., description="告警消息")
    timestamp: datetime = Field(..., description="告警时间")
    resolved: bool = Field(default=False, description="是否已解决")


class AlertListResponse(BaseModel):
    """告警列表响应"""
    alerts: List[AlertInfo] = Field(..., description="告警列表")
    total: int = Field(..., description="总数")
    unresolved: int = Field(..., description="未解决数量")
