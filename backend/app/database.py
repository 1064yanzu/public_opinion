"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import settings

# 创建异步引擎
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# 创建同步引擎（用于 Alembic 迁移）
sync_engine = create_engine(
    settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"),
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=settings.DEBUG,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 同步会话工厂（用于迁移脚本）
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# 声明基类
Base = declarative_base()


# 依赖注入：获取异步数据库会话
async def get_db() -> AsyncSession:
    """
    异步数据库会话依赖
    用于 FastAPI 路由中的依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 同步数据库会话（用于迁移脚本）
def get_sync_db():
    """同步数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 初始化数据库
async def init_db():
    """创建所有数据库表"""
    async with async_engine.begin() as conn:
        # 导入所有模型
        from app.models import user, task, weibo, douyin, hotspot, scheduled_job  # noqa: F401
        
        # 创建表
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_runtime_columns(conn)
        
        # 启用 WAL 模式（提升并发性能）
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))


async def _ensure_runtime_columns(conn):
    """在 SQLite 中补齐后续新增字段，避免桌面端老库无迁移能力。"""

    table_columns = {
        "weibo_data": {
            "gender": "TEXT",
            "province": "TEXT",
            "city": "TEXT",
            "country": "TEXT",
        },
        "douyin_data": {
            "followers_count": "INTEGER DEFAULT 0",
            "province": "TEXT",
            "city": "TEXT",
            "gender": "TEXT",
        },
        "scheduled_jobs": {
            "use_smart_schedule": "BOOLEAN NOT NULL DEFAULT 1",
        },
    }

    for table_name, columns in table_columns.items():
        result = await conn.execute(text(f"PRAGMA table_info({table_name});"))
        existing = {row[1] for row in result.fetchall()}

        for column_name, definition in columns.items():
            if column_name in existing:
                continue
            await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition};"))


# 关闭数据库连接
async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()
