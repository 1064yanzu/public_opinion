"""
配置管理模块。

为兼容桌面端持久化配置，`settings` 使用稳定代理对象。
模块内其他文件即使 `from app.config import settings`，仍然可以在
运行时读取到最新的配置快照。
"""
from __future__ import annotations

from functools import cached_property
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import RuntimePaths, ensure_runtime_directories, resolve_runtime_paths
from app.core.runtime_config import RuntimeConfig, RuntimeConfigStore


class EnvironmentSettings(BaseSettings):
    """环境变量配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "舆情分析系统"
    VERSION: str = "2.1.0"
    DEBUG: bool = True

    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ]
    )

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    DESKTOP_MODE: bool = False
    APP_DATA_DIR: str | None = None
    RUNTIME_CONFIG_PATH: str | None = None

    DATABASE_PATH: str | None = None
    DATA_DIR: str | None = None
    STATIC_DIR: str | None = None
    WORDCLOUD_DIR: str | None = None
    REPORTS_DIR: str | None = None
    UPLOAD_DIR: str | None = None
    LOG_DIR: str | None = None

    SECRET_KEY: str = "your-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    AI_MODEL_TYPE: str = "zhipuai"
    AI_API_KEY: str = ""
    AI_BASE_URL: str = ""
    AI_MODEL_ID: str = ""
    WEIBO_COOKIE: str = ""
    WEIBO_COOKIE: str = ""

    ENABLE_CACHE: bool = True
    CACHE_DURATION: int = 300
    MAX_WORKERS: int = 4

    CRAWLER_MAX_PAGE: int = 50
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_DELAY: float = 1.0
    DOUYIN_COOKIE: str = ""

    ENABLE_MONITORING: bool = True
    MONITORING_INTERVAL: int = 60

    @field_validator("DEBUG", "DESKTOP_MODE", mode="before")
    @classmethod
    def normalize_bool_flags(cls, value: Any):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False
        return value


class SettingsSnapshot(BaseModel):
    """生效中的配置快照。"""

    APP_NAME: str
    VERSION: str
    DEBUG: bool
    ALLOWED_ORIGINS: list[str]
    API_HOST: str
    API_PORT: int
    DESKTOP_MODE: bool
    APP_DATA_DIR: str
    RUNTIME_CONFIG_PATH: str
    DATABASE_PATH: str
    DATABASE_URL: str
    DATA_DIR: str
    STATIC_DIR: str
    WORDCLOUD_DIR: str
    REPORTS_DIR: str
    UPLOAD_DIR: str
    LOG_DIR: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    AI_MODEL_TYPE: str
    AI_API_KEY: str
    AI_BASE_URL: str
    AI_MODEL_ID: str
    WEIBO_COOKIE: str
    ENABLE_CACHE: bool
    CACHE_DURATION: int
    MAX_WORKERS: int
    CRAWLER_MAX_PAGE: int
    CRAWLER_TIMEOUT: int
    CRAWLER_DELAY: float
    DOUYIN_COOKIE: str
    ENABLE_MONITORING: bool
    MONITORING_INTERVAL: int


_RESTART_SENSITIVE_FIELDS = {
    "data_dir",
    "static_dir",
    "wordcloud_dir",
    "reports_dir",
    "upload_dir",
    "database_path",
    "log_dir",
}


class SettingsProxy:
    """稳定的运行时配置代理。"""

    def __init__(self) -> None:
        self._env: EnvironmentSettings | None = None
        self._runtime_config: RuntimeConfig = RuntimeConfig()
        self._paths: RuntimePaths | None = None
        self._snapshot: SettingsSnapshot | None = None
        self.reload()

    def _load_snapshot(
        self,
        *,
        env: EnvironmentSettings,
        runtime_config: RuntimeConfig,
    ) -> tuple[RuntimePaths, SettingsSnapshot]:
        paths = resolve_runtime_paths(
            desktop_mode=env.DESKTOP_MODE,
            app_data_dir=env.APP_DATA_DIR,
            config_path=env.RUNTIME_CONFIG_PATH,
            data_dir=runtime_config.data_dir or env.DATA_DIR,
            static_dir=runtime_config.static_dir or env.STATIC_DIR,
            wordcloud_dir=runtime_config.wordcloud_dir or env.WORDCLOUD_DIR,
            reports_dir=runtime_config.reports_dir or env.REPORTS_DIR,
            upload_dir=runtime_config.upload_dir or env.UPLOAD_DIR,
            database_path=runtime_config.database_path or env.DATABASE_PATH,
            log_dir=runtime_config.log_dir or env.LOG_DIR,
        )
        ensure_runtime_directories(paths)

        snapshot = SettingsSnapshot(
            APP_NAME=runtime_config.app_name or env.APP_NAME,
            VERSION=env.VERSION,
            DEBUG=env.DEBUG,
            ALLOWED_ORIGINS=env.ALLOWED_ORIGINS,
            API_HOST=env.API_HOST,
            API_PORT=env.API_PORT,
            DESKTOP_MODE=env.DESKTOP_MODE,
            APP_DATA_DIR=str(paths.app_data_dir),
            RUNTIME_CONFIG_PATH=str(paths.config_path),
            DATABASE_PATH=str(paths.database_path),
            DATABASE_URL=f"sqlite+aiosqlite:///{paths.database_path}",
            DATA_DIR=str(paths.data_dir),
            STATIC_DIR=str(paths.static_dir),
            WORDCLOUD_DIR=str(paths.wordcloud_dir),
            REPORTS_DIR=str(paths.reports_dir),
            UPLOAD_DIR=str(paths.upload_dir),
            LOG_DIR=str(paths.log_dir),
            SECRET_KEY=env.SECRET_KEY,
            ALGORITHM=env.ALGORITHM,
            ACCESS_TOKEN_EXPIRE_MINUTES=env.ACCESS_TOKEN_EXPIRE_MINUTES,
            AI_MODEL_TYPE=runtime_config.ai_model_type or env.AI_MODEL_TYPE,
            AI_API_KEY=runtime_config.ai_api_key or env.AI_API_KEY,
            AI_BASE_URL=runtime_config.ai_base_url or env.AI_BASE_URL,
            AI_MODEL_ID=runtime_config.ai_model_id or env.AI_MODEL_ID,
            WEIBO_COOKIE=runtime_config.weibo_cookie or env.WEIBO_COOKIE,
            ENABLE_CACHE=env.ENABLE_CACHE,
            CACHE_DURATION=env.CACHE_DURATION,
            MAX_WORKERS=env.MAX_WORKERS,
            CRAWLER_MAX_PAGE=runtime_config.crawler_max_page or env.CRAWLER_MAX_PAGE,
            CRAWLER_TIMEOUT=runtime_config.crawler_timeout or env.CRAWLER_TIMEOUT,
            CRAWLER_DELAY=runtime_config.crawler_delay or env.CRAWLER_DELAY,
            DOUYIN_COOKIE=runtime_config.douyin_cookie or env.DOUYIN_COOKIE,
            ENABLE_MONITORING=env.ENABLE_MONITORING,
            MONITORING_INTERVAL=env.MONITORING_INTERVAL,
        )

        return paths, snapshot

    @cached_property
    def env_loader(self) -> type[EnvironmentSettings]:
        return EnvironmentSettings

    def reload(self) -> SettingsSnapshot:
        env = self.env_loader()
        initial_paths = resolve_runtime_paths(
            desktop_mode=env.DESKTOP_MODE,
            app_data_dir=env.APP_DATA_DIR,
            config_path=env.RUNTIME_CONFIG_PATH,
            data_dir=env.DATA_DIR,
            static_dir=env.STATIC_DIR,
            wordcloud_dir=env.WORDCLOUD_DIR,
            reports_dir=env.REPORTS_DIR,
            upload_dir=env.UPLOAD_DIR,
            database_path=env.DATABASE_PATH,
            log_dir=env.LOG_DIR,
        )
        ensure_runtime_directories(initial_paths)

        store = RuntimeConfigStore(initial_paths.config_path)
        runtime_config = store.load()
        paths, snapshot = self._load_snapshot(env=env, runtime_config=runtime_config)

        self._env = env
        self._runtime_config = runtime_config
        self._paths = paths
        self._snapshot = snapshot
        return snapshot

    @property
    def paths(self) -> RuntimePaths:
        assert self._paths is not None
        return self._paths

    @property
    def runtime_config(self) -> RuntimeConfig:
        return self._runtime_config

    @property
    def store(self) -> RuntimeConfigStore:
        return RuntimeConfigStore(self.paths.config_path)

    def snapshot(self) -> SettingsSnapshot:
        assert self._snapshot is not None
        return self._snapshot

    def runtime_config_dump(self) -> dict[str, Any]:
        return self.runtime_config.model_dump()

    def update_runtime_config(self, patch: dict[str, Any]) -> tuple[SettingsSnapshot, RuntimeConfig, bool]:
        previous = self.runtime_config
        updated_runtime = self.store.update(patch)
        restart_required = any(
            getattr(previous, field) != getattr(updated_runtime, field)
            for field in _RESTART_SENSITIVE_FIELDS
        )

        env = self.env_loader()
        paths, snapshot = self._load_snapshot(env=env, runtime_config=updated_runtime)
        self._env = env
        self._runtime_config = updated_runtime
        self._paths = paths
        self._snapshot = snapshot
        return snapshot, updated_runtime, restart_required

    def __getattr__(self, item: str) -> Any:
        snapshot = self.snapshot()
        return getattr(snapshot, item)


settings = SettingsProxy()
