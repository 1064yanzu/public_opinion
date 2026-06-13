"""
桌面端后端启动入口。

在 PyInstaller frozen 环境下，添加顶层异常处理和日志
确保崩溃信息能被看到（写入 stderr 和临时日志文件）。
"""
from __future__ import annotations

import logging
import os
import sys
import traceback

# Windows 编码修复：强制使用 UTF-8
if sys.platform == "win32":
    try:
        # 重新配置标准输出和错误输出为 UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')

        # 设置环境变量确保子进程也使用 UTF-8
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except Exception:
        pass  # 静默失败，不阻碍启动


def _setup_frozen_logging():
    """为 frozen 环境配置一个最基本的文件日志，写到用户可见的位置。"""
    if not getattr(sys, "frozen", False):
        return

    try:
        log_dir = os.path.join(os.path.expanduser("~"), ".public_opinion_desktop", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "backend_crash.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)
    except Exception:
        pass  # 日志初始化本身不应阻断启动


def main():
    """桌面后端主入口。"""
    _setup_frozen_logging()

    try:
        import uvicorn

        from app.main import app
        from app.config import settings

        # 桌面模式: 单 worker, 关闭 access log, 尝试用 httptools 加速
        uvicorn.run(
            app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=False,
            workers=1,
            access_log=False,
            log_level="warning" if not settings.DEBUG else "debug",
            timeout_keep_alive=30,
        )
    except Exception as exc:
        error_msg = f"后端启动失败:\n{traceback.format_exc()}"
        logging.getLogger(__name__).critical(error_msg)
        print(error_msg, file=sys.stderr)

        # 再次尝试写到用户可见位置
        try:
            log_dir = os.path.join(os.path.expanduser("~"), ".public_opinion_desktop", "logs")
            os.makedirs(log_dir, exist_ok=True)
            crash_file = os.path.join(log_dir, "backend_crash.log")
            with open(crash_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n{error_msg}\n")
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
