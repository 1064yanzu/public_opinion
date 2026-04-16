"""
桌面端系统配置与运行时状态路由。
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas import DesktopRuntimeResponse, SystemConfigPayload, SystemConfigResponse
from app.services.weibo_spider import WeiboSpider

router = APIRouter()


class WeiboConnectionTestResponse(BaseModel):
    success: bool = Field(..., description="测试是否成功")
    mode: str = Field(..., description="当前使用模式：cookie/visitor")
    message: str = Field(..., description="测试结果说明")
    sample_count: int = Field(default=0, description="采样结果数")


def _build_config_payload() -> SystemConfigPayload:
    return SystemConfigPayload.model_validate(settings.runtime_config_dump())


@router.get("/config", response_model=SystemConfigResponse, summary="获取系统配置")
async def get_system_config():
    """返回当前保存的系统配置与生效中的运行时快照。"""
    return SystemConfigResponse(
        config=_build_config_payload(),
        active_runtime=settings.snapshot().model_dump(),
        config_path=settings.RUNTIME_CONFIG_PATH,
        restart_required=False,
    )


@router.put("/config", response_model=SystemConfigResponse, summary="更新系统配置")
async def update_system_config(payload: SystemConfigPayload):
    """更新系统配置文件。"""
    patch = payload.model_dump(exclude_none=True)
    snapshot, runtime_config, restart_required = settings.update_runtime_config(patch)
    return SystemConfigResponse(
        config=SystemConfigPayload.model_validate(runtime_config.model_dump()),
        active_runtime=snapshot.model_dump(),
        config_path=settings.RUNTIME_CONFIG_PATH,
        restart_required=restart_required,
    )


@router.get("/runtime", response_model=DesktopRuntimeResponse, summary="获取运行时状态")
async def get_runtime_status():
    """获取当前后端运行环境。"""
    return DesktopRuntimeResponse(
        desktop_mode=settings.DESKTOP_MODE,
        api_host=settings.API_HOST,
        api_port=settings.API_PORT,
        app_data_dir=settings.APP_DATA_DIR,
        static_dir=settings.STATIC_DIR,
        reports_dir=settings.REPORTS_DIR,
        wordcloud_dir=settings.WORDCLOUD_DIR,
        database_path=settings.DATABASE_PATH,
        config_path=settings.RUNTIME_CONFIG_PATH,
        log_dir=settings.LOG_DIR,
    )


@router.get("/weibo-connection-test", response_model=WeiboConnectionTestResponse, summary="测试微博连接")
async def test_weibo_connection():
    """测试当前微博采集配置是否可用。"""
    spider = WeiboSpider(cookie=settings.WEIBO_COOKIE)
    rows = spider._crawl_page("小米", 1)
    using_cookie = bool(settings.WEIBO_COOKIE)
    mode = "cookie" if using_cookie else "visitor"

    if rows:
        return WeiboConnectionTestResponse(
            success=True,
            mode=mode,
            message="微博搜索接口可用，当前配置可以拿到真实结果。",
            sample_count=len(rows),
        )

    return WeiboConnectionTestResponse(
        success=False,
        mode=mode,
        message=spider.last_error or "微博连接测试失败，请检查当前配置。",
        sample_count=0,
    )
