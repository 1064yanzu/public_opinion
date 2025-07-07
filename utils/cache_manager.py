"""
缓存管理模块 - 提供内存缓存功能以提升性能
"""
import time
import threading
import hashlib
import json
import gc
from functools import wraps
from typing import Any, Optional, Dict, Callable
from config.settings import PERFORMANCE_CONFIG


class MemoryCache:
    """内存缓存类，线程安全"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._access_times: Dict[str, float] = {}
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float) -> bool:
        """检查是否过期"""
        return time.time() - timestamp > self.ttl
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self._cache.items():
            if current_time - data['timestamp'] > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
    
    def _evict_lru(self):
        """LRU淘汰策略"""
        if len(self._cache) >= self.max_size:
            # 找到最少使用的键
            lru_key = min(self._access_times.keys(), 
                         key=lambda k: self._access_times[k])
            self._cache.pop(lru_key, None)
            self._access_times.pop(lru_key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return None
            
            data = self._cache[key]
            if self._is_expired(data['timestamp']):
                self._cache.pop(key, None)
                self._access_times.pop(key, None)
                return None
            
            # 更新访问时间
            self._access_times[key] = time.time()
            return data['value']
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        with self._lock:
            # 清理过期缓存
            self._cleanup_expired()
            
            # LRU淘汰
            self._evict_lru()
            
            # 设置新值
            self._cache[key] = {
                'value': value,
                'timestamp': time.time()
            }
            self._access_times[key] = time.time()
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            gc.collect()  # 强制垃圾回收
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'ttl': self.ttl,
                'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_count', 1), 1)
            }


# 全局缓存实例
_global_cache = MemoryCache(
    max_size=PERFORMANCE_CONFIG.get('max_cache_size', 1000),
    ttl=PERFORMANCE_CONFIG.get('cache_ttl', 3600)
)


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒），None使用默认值
        key_prefix: 缓存键前缀
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not PERFORMANCE_CONFIG.get('cache_enabled', True):
                return func(*args, **kwargs)
            
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{_global_cache._generate_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_result = _global_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator


def cache_csv_data(csv_path: str, data: Any):
    """缓存CSV数据"""
    key = f"csv_data:{csv_path}:{hash(str(data))}"
    _global_cache.set(key, data)


def get_cached_csv_data(csv_path: str) -> Optional[Any]:
    """获取缓存的CSV数据"""
    # 这里简化处理，实际应该根据文件修改时间判断
    import os
    if not os.path.exists(csv_path):
        return None
    
    file_mtime = os.path.getmtime(csv_path)
    key = f"csv_data:{csv_path}:{file_mtime}"
    return _global_cache.get(key)


def clear_cache():
    """清空所有缓存"""
    _global_cache.clear()


def get_cache_stats() -> Dict:
    """获取缓存统计信息"""
    return _global_cache.get_stats()


# 内存监控函数
def get_memory_usage() -> Dict:
    """获取内存使用情况"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # 物理内存
        'vms_mb': memory_info.vms / 1024 / 1024,  # 虚拟内存
        'percent': process.memory_percent(),       # 内存使用百分比
        'cache_size': len(_global_cache._cache)    # 缓存条目数
    }


def memory_cleanup():
    """内存清理"""
    clear_cache()
    gc.collect()
