"""
缓存服务

使用 cachetools 提供内存缓存功能，支持 TTL 过期和 LRU 淘汰策略
"""
import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional

try:
    import cachetools
    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False
    print("警告: cachetools 未安装，缓存功能不可用。请运行: pip install cachetools")

from app.config import settings


class CacheService:
    """缓存服务类"""

    def __init__(self, maxsize: int = 100, ttl: int = 300):
        """
        初始化缓存服务

        Args:
            maxsize: 缓存最大条目数
            ttl: 缓存过期时间（秒）
        """
        if CACHETOOLS_AVAILABLE:
            self.cache = cachetools.TTLCache(maxsize=maxsize, ttl=ttl)
            self.enabled = settings.ENABLE_CACHE
        else:
            self.cache = {}
            self.enabled = False

        self.hits = 0
        self.misses = 0

    def _generate_key(self, *args, **kwargs) -> str:
        """
        生成缓存键

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存键（MD5 哈希）
        """
        # 将参数序列化为字符串
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回 None
        """
        if not self.enabled:
            return None

        value = self.cache.get(key)
        if value is not None:
            self.hits += 1
        else:
            self.misses += 1

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        if not self.enabled:
            return

        self.cache[key] = value

    def delete(self, key: str) -> None:
        """
        删除缓存

        Args:
            key: 缓存键
        """
        if not self.enabled:
            return

        self.cache.pop(key, None)

    def clear(self) -> None:
        """清空所有缓存"""
        if not self.enabled:
            return

        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            包含 hits、misses、size 的字典
        """
        return {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "size": len(self.cache),
            "hit_rate": round(self.hits / (self.hits + self.misses) * 100, 2) if (self.hits + self.misses) > 0 else 0
        }


# 全局缓存实例
_cache_service = CacheService(maxsize=100, ttl=settings.CACHE_DURATION)


def get_cache_service() -> CacheService:
    """获取缓存服务单例"""
    return _cache_service


def cached(key_func: Optional[Callable] = None):
    """
    缓存装饰器

    用于缓存异步函数的返回值

    Args:
        key_func: 自定义键生成函数，接收被装饰函数的参数，返回缓存键

    Example:
        @cached(lambda keyword: f"wordcloud:{keyword}")
        async def generate_wordcloud(keyword: str):
            # 耗时操作
            return result
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()

            if not cache.enabled:
                # 缓存未启用，直接调用函数
                return await func(*args, **kwargs)

            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._generate_key(func.__name__, *args, **kwargs)

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 缓存未命中，调用函数
            result = await func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result)

            return result

        return wrapper
    return decorator
