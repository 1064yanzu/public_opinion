"""
数据模型包初始化
导入所有模型以便 Alembic 自动检测
"""
from app.models.user import User
from app.models.task import Task
from app.models.weibo import WeiboData
from app.models.douyin import DouyinData
from app.models.hotspot import Hotspot

__all__ = ["User", "Task", "WeiboData", "DouyinData", "Hotspot"]
