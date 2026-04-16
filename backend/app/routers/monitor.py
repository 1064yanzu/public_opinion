"""
系统监控相关 API 路由
"""
import psutil
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas import (
    PerformanceStats, CacheStats, AlertInfo, AlertListResponse, MessageResponse
)
from app.config import settings

router = APIRouter()

# 应用启动时间
START_TIME = time.time()

# 简单的内存缓存统计
_cache_stats = {
    "total_size": 0,
    "item_count": 0,
    "hits": 0,
    "misses": 0,
}

# 告警历史
_alert_history = []


@router.get("/health", summary="健康检查", description="检查系统健康状态")
async def health_check():
    """
    健康检查
    
    返回系统运行状态和版本信息
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": int(time.time() - START_TIME),
    }


@router.get("/performance", response_model=PerformanceStats, summary="性能统计",
            description="获取系统性能统计信息")
async def get_performance_stats(current_user: User = Depends(get_current_user)):
    """
    获取性能统计
    
    包括 CPU、内存、磁盘使用率和运行时间
    """
    return PerformanceStats(
        cpu_usage=psutil.cpu_percent(interval=0.1),
        memory_usage=psutil.virtual_memory().percent,
        disk_usage=psutil.disk_usage('/').percent,
        uptime=int(time.time() - START_TIME),
    )


@router.get("/cache", response_model=CacheStats, summary="缓存统计",
            description="获取缓存统计信息")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """获取缓存统计信息"""
    total_requests = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = _cache_stats["hits"] / total_requests if total_requests > 0 else 0
    
    return CacheStats(
        total_size=_cache_stats["total_size"],
        item_count=_cache_stats["item_count"],
        hit_rate=round(hit_rate, 4),
    )


@router.post("/cache/clear", response_model=MessageResponse, summary="清空缓存",
             description="清空系统缓存")
async def clear_cache(current_user: User = Depends(get_current_user)):
    """清空缓存"""
    global _cache_stats
    old_count = _cache_stats["item_count"]
    _cache_stats = {
        "total_size": 0,
        "item_count": 0,
        "hits": 0,
        "misses": 0,
    }
    
    return MessageResponse(message=f"缓存已清空，共清除 {old_count} 项", success=True)


@router.get("/alerts", response_model=AlertListResponse, summary="获取告警",
            description="获取系统告警信息")
async def get_alerts(
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_user)
):
    """获取告警列表"""
    alerts = _alert_history[-limit:]
    unresolved = sum(1 for a in alerts if not a.get("resolved", False))
    
    alert_list = [
        AlertInfo(
            id=a["id"],
            level=a["level"],
            type=a["type"],
            message=a["message"],
            timestamp=a["timestamp"],
            resolved=a.get("resolved", False),
        )
        for a in alerts
    ]
    
    return AlertListResponse(
        alerts=alert_list,
        total=len(alerts),
        unresolved=unresolved,
    )


@router.post("/alerts/check", response_model=MessageResponse, summary="检查告警",
             description="手动触发告警检查")
async def check_alerts(current_user: User = Depends(get_current_user)):
    """手动检查告警"""
    alerts_triggered = []
    
    # 检查 CPU
    cpu_usage = psutil.cpu_percent(interval=0.1)
    if cpu_usage > 80:
        alert = {
            "id": f"cpu_{int(time.time())}",
            "level": "warning",
            "type": "cpu_high",
            "message": f"CPU 使用率过高: {cpu_usage}%",
            "timestamp": datetime.utcnow(),
            "resolved": False,
        }
        _alert_history.append(alert)
        alerts_triggered.append(alert["message"])
    
    # 检查内存
    memory_usage = psutil.virtual_memory().percent
    if memory_usage > 80:
        alert = {
            "id": f"memory_{int(time.time())}",
            "level": "warning",
            "type": "memory_high",
            "message": f"内存使用率过高: {memory_usage}%",
            "timestamp": datetime.utcnow(),
            "resolved": False,
        }
        _alert_history.append(alert)
        alerts_triggered.append(alert["message"])
    
    # 检查磁盘
    disk_usage = psutil.disk_usage('/').percent
    if disk_usage > 90:
        alert = {
            "id": f"disk_{int(time.time())}",
            "level": "error",
            "type": "disk_high",
            "message": f"磁盘使用率过高: {disk_usage}%",
            "timestamp": datetime.utcnow(),
            "resolved": False,
        }
        _alert_history.append(alert)
        alerts_triggered.append(alert["message"])
    
    if alerts_triggered:
        return MessageResponse(
            message=f"触发 {len(alerts_triggered)} 个告警: {', '.join(alerts_triggered)}",
            success=True
        )
    else:
        return MessageResponse(message="系统正常，无告警", success=True)


@router.get("/system", summary="系统信息", description="获取系统详细信息")
async def get_system_info(current_user: User = Depends(get_current_user)):
    """获取系统详细信息"""
    import platform
    
    return {
        "system": platform.system(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_total": psutil.disk_usage('/').total,
        "disk_free": psutil.disk_usage('/').free,
        "uptime": int(time.time() - START_TIME),
        "start_time": datetime.fromtimestamp(START_TIME).isoformat(),
    }
