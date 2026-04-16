"""
桌面端后端启动入口。
"""
from __future__ import annotations

import uvicorn

from app.main import app
from app.config import settings


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level="debug" if settings.DEBUG else "info",
    )
