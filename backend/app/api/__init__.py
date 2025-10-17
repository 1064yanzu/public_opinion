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

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["datasets"])
api_router.include_router(records_router, prefix="/records", tags=["records"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(spider_router, prefix="/spider", tags=["spider"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(wordcloud_router, prefix="/wordcloud", tags=["wordcloud"])
