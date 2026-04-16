"""
FastAPI 主应用。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import close_db, init_db


logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    logger.info("应用启动中...")
    try:
        await init_db()
        logger.info("数据库初始化成功")
    except Exception as exc:  # pragma: no cover - 启动日志
        logger.error("数据库初始化失败: %s", exc)

    # 启动定时采集调度器，恢复持久化的定时任务
    try:
        from app.services.scheduler import scheduler_service
        await scheduler_service.start()
        logger.info("定时采集调度器已启动")
    except Exception as exc:
        logger.error("调度器启动失败: %s", exc)

    yield

    logger.info("应用关闭中...")
    # 优雅停止调度器
    try:
        from app.services.scheduler import scheduler_service
        await scheduler_service.stop()
        logger.info("调度器已停止")
    except Exception as exc:
        logger.error("调度器停止时出错: %s", exc)

    await close_db()
    logger.info("数据库连接已关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例。"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="基于 FastAPI 的舆情分析系统后端 API",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
    app.mount("/static/reports", StaticFiles(directory=settings.REPORTS_DIR), name="reports")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers import auth, spider, analysis, monitor, page, ai, advanced, dashboard, reports, system
    from app.routers import scheduler

    app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
    app.include_router(spider.router, prefix="/api/spider", tags=["爬虫"])
    app.include_router(scheduler.router, prefix="/api/scheduler", tags=["定时采集"])
    app.include_router(analysis.router, prefix="/api/analysis", tags=["分析"])
    app.include_router(monitor.router, prefix="/api/monitor", tags=["监控"])
    app.include_router(page.router, prefix="/api/page", tags=["页面数据"])
    app.include_router(ai.router, prefix="/api/ai", tags=["AI助手"])
    app.include_router(advanced.router, prefix="/api/advanced", tags=["高级分析"])
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘"])
    app.include_router(reports.router, prefix="/api/reports", tags=["报告"])
    app.include_router(system.router, prefix="/api/system", tags=["系统"])

    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.VERSION,
            "desktop_mode": settings.DESKTOP_MODE,
            "api_port": settings.API_PORT,
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("未处理的异常: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误",
                "error": str(exc) if settings.DEBUG else "Internal Server Error",
            },
        )

    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info("%s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("Status: %s", response.status_code)
        return response

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("启动 %s v%s", settings.APP_NAME, settings.VERSION)
    logger.info("文档地址: http://%s:%s/docs", settings.API_HOST, settings.API_PORT)

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
