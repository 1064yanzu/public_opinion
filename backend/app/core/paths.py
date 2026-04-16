"""
桌面端与 Web 端共享的路径解析工具。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent.parent


@dataclass(frozen=True)
class RuntimePaths:
    """运行时路径集合。"""

    app_data_dir: Path
    config_dir: Path
    config_path: Path
    data_dir: Path
    static_dir: Path
    wordcloud_dir: Path
    reports_dir: Path
    upload_dir: Path
    database_path: Path
    log_dir: Path


def _normalize_path(value: str | None, fallback: Path) -> Path:
    if not value:
        return fallback

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def resolve_runtime_paths(
    *,
    desktop_mode: bool,
    app_data_dir: str | None,
    config_path: str | None,
    data_dir: str | None,
    static_dir: str | None,
    wordcloud_dir: str | None,
    reports_dir: str | None,
    upload_dir: str | None,
    database_path: str | None,
    log_dir: str | None,
) -> RuntimePaths:
    """根据运行模式解析所有文件系统路径。"""

    if desktop_mode or app_data_dir:
        resolved_app_data_dir = _normalize_path(
            app_data_dir,
            PROJECT_ROOT / ".runtime-desktop",
        )
        resolved_config_dir = resolved_app_data_dir / "config"
        resolved_data_dir = _normalize_path(data_dir, resolved_app_data_dir / "data")
        resolved_static_dir = _normalize_path(static_dir, resolved_app_data_dir / "static")
        resolved_reports_dir = _normalize_path(reports_dir, resolved_app_data_dir / "reports")
        resolved_wordcloud_dir = _normalize_path(wordcloud_dir, resolved_static_dir / "wordcloud")
        resolved_upload_dir = _normalize_path(upload_dir, resolved_app_data_dir / "uploads")
        resolved_database_path = _normalize_path(
            database_path,
            resolved_app_data_dir / "database" / "public_opinion.db",
        )
        resolved_log_dir = _normalize_path(log_dir, resolved_app_data_dir / "logs")
        resolved_config_path = _normalize_path(config_path, resolved_config_dir / "runtime-config.json")
    else:
        resolved_app_data_dir = PROJECT_ROOT
        resolved_config_dir = PROJECT_ROOT / "config"
        resolved_data_dir = _normalize_path(data_dir, PROJECT_ROOT / "data")
        resolved_static_dir = _normalize_path(static_dir, PROJECT_ROOT / "static")
        resolved_reports_dir = _normalize_path(reports_dir, PROJECT_ROOT / "reports")
        resolved_wordcloud_dir = _normalize_path(wordcloud_dir, resolved_static_dir / "wordcloud")
        resolved_upload_dir = _normalize_path(upload_dir, BACKEND_DIR / "uploads")
        resolved_database_path = _normalize_path(database_path, BACKEND_DIR / "public_opinion.db")
        resolved_log_dir = _normalize_path(log_dir, PROJECT_ROOT / "logs")
        resolved_config_path = _normalize_path(config_path, resolved_config_dir / "runtime-config.json")

    return RuntimePaths(
        app_data_dir=resolved_app_data_dir,
        config_dir=resolved_config_dir,
        config_path=resolved_config_path,
        data_dir=resolved_data_dir,
        static_dir=resolved_static_dir,
        wordcloud_dir=resolved_wordcloud_dir,
        reports_dir=resolved_reports_dir,
        upload_dir=resolved_upload_dir,
        database_path=resolved_database_path,
        log_dir=resolved_log_dir,
    )


def ensure_runtime_directories(paths: RuntimePaths) -> None:
    """确保运行期需要的目录存在。"""

    directories = (
        paths.config_dir,
        paths.data_dir,
        paths.static_dir,
        paths.wordcloud_dir,
        paths.reports_dir,
        paths.upload_dir,
        paths.database_path.parent,
        paths.log_dir,
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

