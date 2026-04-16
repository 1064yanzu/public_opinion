"""
桌面运行时配置读写。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class RuntimeConfig(BaseModel):
    """可由桌面端用户修改的配置。"""

    model_config = ConfigDict(extra="ignore")

    app_name: str | None = None
    ai_model_type: str | None = None
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model_id: str | None = None
    weibo_cookie: str | None = None
    douyin_cookie: str | None = None
    crawler_max_page: int | None = None
    crawler_timeout: int | None = None
    crawler_delay: float | None = None
    data_dir: str | None = None
    static_dir: str | None = None
    wordcloud_dir: str | None = None
    reports_dir: str | None = None
    upload_dir: str | None = None
    database_path: str | None = None
    log_dir: str | None = None


class RuntimeConfigStore:
    """运行时配置文件存储。"""

    def __init__(self, config_path: Path):
        self.config_path = config_path

    def load(self) -> RuntimeConfig:
        if not self.config_path.exists():
            return RuntimeConfig()

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return RuntimeConfig()

        if not isinstance(data, dict):
            return RuntimeConfig()

        return RuntimeConfig.model_validate(data)

    def save(self, config: RuntimeConfig) -> RuntimeConfig:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = config.model_dump(exclude_none=True)
        self.config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return config

    def update(self, patch: dict[str, Any]) -> RuntimeConfig:
        current = self.load()
        updated = current.model_copy(update=patch)
        return self.save(updated)
