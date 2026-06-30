"""
FastAPI 主应用。
"""
import asyncio
import logging
import logging.handlers
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import close_db, init_db

# Windows 编码修复：确保日志输出使用 UTF-8
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def _setup_logging() -> None:
    """配置带轮转的日志输出，避免长期运行日志膨胀到 GB 级。"""
    root = logging.getLogger()
    root.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 移除已存在的同源 handler，避免重启时重复
    for handler in list(root.handlers):
        root.removeHandler(handler)

    # 控制台输出（桌面端会被 Tauri 重定向到 backend.log）
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    root.addHandler(stream_handler)

    # 文件日志：10MB × 5 份，最多占 50MB
    try:
        log_dir = settings.LOG_DIR
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except Exception as exc:  # 不阻塞启动
        root.warning("RotatingFileHandler 初始化失败: %s", exc)


_setup_logging()
logger = logging.getLogger(__name__)


async def _periodic_storage_maintenance() -> None:
    """每 6 小时执行：清理过期词云图、checkpoint WAL、optimize。"""
    from datetime import datetime, timedelta
    from sqlalchemy import text
    from app.database import async_engine

    while True:
        try:
            # === 1. 清理 7 天前的词云图片 ===
            try:
                wc_dir = settings.WORDCLOUD_DIR
                cutoff = datetime.now() - timedelta(days=7)
                if os.path.isdir(wc_dir):
                    removed = 0
                    for name in os.listdir(wc_dir):
                        full = os.path.join(wc_dir, name)
                        if not os.path.isfile(full):
                            continue
                        try:
                            mtime = datetime.fromtimestamp(os.path.getmtime(full))
                            if mtime < cutoff:
                                os.remove(full)
                                removed += 1
                        except OSError:
                            continue
                    if removed:
                        logger.info("清理过期词云图片: %d 张", removed)
            except Exception as exc:
                logger.warning("词云清理失败: %s", exc)

            # === 2. 清理 7 天前的报告 ===
            try:
                rp_dir = settings.REPORTS_DIR
                cutoff = datetime.now() - timedelta(days=7)
                if os.path.isdir(rp_dir):
                    removed = 0
                    for name in os.listdir(rp_dir):
                        full = os.path.join(rp_dir, name)
                        if not os.path.isfile(full):
                            continue
                        try:
                            mtime = datetime.fromtimestamp(os.path.getmtime(full))
                            if mtime < cutoff:
                                os.remove(full)
                                removed += 1
                        except OSError:
                            continue
                    if removed:
                        logger.info("清理过期报告: %d 份", removed)
            except Exception as exc:
                logger.warning("报告清理失败: %s", exc)

            # === 3. SQLite checkpoint + optimize ===
            try:
                async with async_engine.begin() as conn:
                    await conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE);"))
                    await conn.execute(text("PRAGMA optimize;"))
                logger.debug("SQLite wal_checkpoint + optimize 完成")
            except Exception as exc:
                logger.warning("SQLite 维护失败: %s", exc)

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("存储维护任务异常: %s", exc)

        # 每 6 小时跑一次
        await asyncio.sleep(6 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    logger.info("应用启动中...")
    try:
        await init_db()
        logger.info("数据库初始化成功")
    except Exception as exc:
        logger.error("数据库初始化失败: %s", exc)

    # 启动定时采集调度器 — 用 create_task 不阻塞 lifespan，
    # 让 FastAPI 立刻准备好响应 health 检查，前端尽快越过启动屏。
    scheduler_task: asyncio.Task | None = None

    async def _start_scheduler():
        try:
            from app.services.scheduler import scheduler_service
            await scheduler_service.start()
            logger.info("定时采集调度器已启动")
        except Exception as exc:
            logger.error("调度器启动失败: %s", exc)

    scheduler_task = asyncio.create_task(_start_scheduler())

    # 启动存储维护后台任务
    maintenance_task = asyncio.create_task(_periodic_storage_maintenance())

    yield

    logger.info("应用关闭中...")

    # 停止维护任务
    maintenance_task.cancel()
    try:
        await maintenance_task
    except (asyncio.CancelledError, Exception):
        pass

    # 等调度器 start 任务结束（如果还没好就放掉）
    if scheduler_task and not scheduler_task.done():
        scheduler_task.cancel()
        try:
            await scheduler_task
        except (asyncio.CancelledError, Exception):
            pass

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
        default_response_class=ORJSONResponse,
    )

    # 确保静态目录存在（frozen/首次启动时可能还未创建）
    os.makedirs(settings.STATIC_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)

    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
    app.mount("/static/reports", StaticFiles(directory=settings.REPORTS_DIR), name="reports")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 路由注册：函数级导入仍然会触发 router 模块加载，但 lifespan 已通过
    # asyncio.create_task 把调度器/维护任务挪出主路径，主要冷启动开销在这。
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
        response = await call_next(request)
        # 只记录非 2xx 响应，减少桌面端日志 I/O
        if response.status_code >= 400:
            logger.warning("%s %s -> %s", request.method, request.url.path, response.status_code)
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
