"""API routes"""
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .datasets import router as datasets_router
from .records import router as records_router
from .analytics import router as analytics_router
from .spider import router as spider_router
from .ai import router as ai_router
from .wordcloud import router as wordcloud_router
from .cases import router as cases_router
from .report import router as report_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["数据集"])
api_router.include_router(records_router, prefix="/records", tags=["数据记录"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["数据分析"])
api_router.include_router(spider_router, prefix="/spider", tags=["爬虫系统"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI助手"])
api_router.include_router(wordcloud_router, prefix="/wordcloud", tags=["词云"])
api_router.include_router(cases_router, prefix="/cases", tags=["案例库"])
api_router.include_router(report_router, prefix="/report", tags=["报告生成"])
