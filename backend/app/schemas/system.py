"""
系统配置与桌面运行时相关的 Schemas。
"""
from pydantic import BaseModel, Field


class SystemConfigPayload(BaseModel):
    """可由前端写入的系统配置。"""

    app_name: str | None = Field(default=None, description="应用显示名称")
    ai_model_type: str | None = Field(default=None, description="AI 服务类型")
    ai_api_key: str | None = Field(default=None, description="AI 服务密钥")
    ai_base_url: str | None = Field(default=None, description="自定义 AI 服务地址")
    ai_model_id: str | None = Field(default=None, description="模型 ID")
    weibo_cookie: str | None = Field(default=None, description="微博 Cookie")
    douyin_cookie: str | None = Field(default=None, description="抖音 Cookie")
    crawler_max_page: int | None = Field(default=None, ge=1, le=100, description="默认最大页数")
    crawler_timeout: int | None = Field(default=None, ge=5, le=300, description="爬虫超时时间")
    crawler_delay: float | None = Field(default=None, ge=0, le=10, description="爬虫请求延迟")
    data_dir: str | None = Field(default=None, description="数据目录")
    static_dir: str | None = Field(default=None, description="静态目录")
    wordcloud_dir: str | None = Field(default=None, description="词云目录")
    reports_dir: str | None = Field(default=None, description="报告目录")
    upload_dir: str | None = Field(default=None, description="上传目录")
    database_path: str | None = Field(default=None, description="数据库文件路径")
    log_dir: str | None = Field(default=None, description="日志目录")


class SystemConfigResponse(BaseModel):
    """返回给前端的完整系统配置。"""

    config: SystemConfigPayload
    active_runtime: dict = Field(default_factory=dict, description="当前运行时快照")
    config_path: str = Field(..., description="配置文件路径")
    restart_required: bool = Field(default=False, description="保存后是否需要重启后端")


class DesktopRuntimeResponse(BaseModel):
    """桌面运行时状态。"""

    desktop_mode: bool = Field(..., description="是否为桌面模式")
    api_host: str = Field(..., description="后端监听地址")
    api_port: int = Field(..., description="后端监听端口")
    app_data_dir: str = Field(..., description="应用数据目录")
    static_dir: str = Field(..., description="静态资源目录")
    reports_dir: str = Field(..., description="报告目录")
    wordcloud_dir: str = Field(..., description="词云目录")
    database_path: str = Field(..., description="数据库文件路径")
    config_path: str = Field(..., description="运行时配置文件路径")
    log_dir: str = Field(..., description="日志目录")
