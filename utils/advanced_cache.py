"""
高级缓存系统 - 多层缓存策略和智能缓存管理
"""
import os
import time
import pickle
import hashlib
import threading
import json
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from utils.cache_manager import MemoryCache
from utils.performance_monitor import monitor_performance
from config.settings import PERFORMANCE_CONFIG


class FileCache:
    """文件缓存层"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.lock = threading.Lock()
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 缓存元数据文件
        self.metadata_file = os.path.join(cache_dir, "metadata.json")
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载缓存元数据"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载缓存元数据失败: {str(e)}")
        
        return {}
    
    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存元数据失败: {str(e)}")
    
    def _get_cache_path(self, key: str) -> str:
        """获取缓存文件路径"""
        # 使用MD5哈希避免文件名过长
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, meta in self.metadata.items():
            if current_time > meta.get('expires_at', 0):
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_cache_file(key)
    
    def _remove_cache_file(self, key: str):
        """删除缓存文件"""
        try:
            cache_path = self._get_cache_path(key)
            if os.path.exists(cache_path):
                os.remove(cache_path)
            
            self.metadata.pop(key, None)
        except Exception as e:
            print(f"删除缓存文件失败: {str(e)}")
    
    def _check_size_limit(self):
        """检查缓存大小限制"""
        total_size = 0
        file_sizes = []
        
        for key, meta in self.metadata.items():
            cache_path = self._get_cache_path(key)
            if os.path.exists(cache_path):
                size = os.path.getsize(cache_path)
                total_size += size
                file_sizes.append((key, size, meta.get('access_time', 0)))
        
        # 如果超过大小限制，删除最少使用的文件
        if total_size > self.max_size_mb * 1024 * 1024:
            # 按访问时间排序，删除最旧的
            file_sizes.sort(key=lambda x: x[2])
            
            for key, size, _ in file_sizes:
                self._remove_cache_file(key)
                total_size -= size
                
                if total_size <= self.max_size_mb * 1024 * 1024 * 0.8:  # 保留80%空间
                    break
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.metadata:
                return None
            
            meta = self.metadata[key]
            
            # 检查是否过期
            if time.time() > meta.get('expires_at', 0):
                self._remove_cache_file(key)
                return None
            
            try:
                cache_path = self._get_cache_path(key)
                if not os.path.exists(cache_path):
                    self.metadata.pop(key, None)
                    return None
                
                with open(cache_path, 'rb') as f:
                    value = pickle.load(f)
                
                # 更新访问时间
                meta['access_time'] = time.time()
                meta['access_count'] = meta.get('access_count', 0) + 1
                
                return value
                
            except Exception as e:
                print(f"读取缓存文件失败: {str(e)}")
                self._remove_cache_file(key)
                return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        with self.lock:
            try:
                # 清理过期缓存
                self._cleanup_expired()
                
                # 检查大小限制
                self._check_size_limit()
                
                cache_path = self._get_cache_path(key)
                
                with open(cache_path, 'wb') as f:
                    pickle.dump(value, f)
                
                # 更新元数据
                self.metadata[key] = {
                    'created_at': time.time(),
                    'expires_at': time.time() + ttl,
                    'access_time': time.time(),
                    'access_count': 1,
                    'size': os.path.getsize(cache_path)
                }
                
                self._save_metadata()
                
            except Exception as e:
                print(f"写入缓存文件失败: {str(e)}")
    
    def clear(self):
        """清空所有缓存"""
        with self.lock:
            try:
                for key in list(self.metadata.keys()):
                    self._remove_cache_file(key)
                
                self.metadata.clear()
                self._save_metadata()
                
            except Exception as e:
                print(f"清空缓存失败: {str(e)}")
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        with self.lock:
            total_size = 0
            total_files = len(self.metadata)
            total_access = 0
            
            for meta in self.metadata.values():
                total_size += meta.get('size', 0)
                total_access += meta.get('access_count', 0)
            
            return {
                'total_files': total_files,
                'total_size_mb': total_size / 1024 / 1024,
                'max_size_mb': self.max_size_mb,
                'total_access': total_access,
                'cache_dir': self.cache_dir
            }


class MultiLevelCache:
    """多层缓存系统"""
    
    def __init__(self):
        # L1: 内存缓存（最快）
        self.l1_cache = MemoryCache(
            max_size=PERFORMANCE_CONFIG.get('l1_cache_size', 500),
            ttl=PERFORMANCE_CONFIG.get('l1_cache_ttl', 300)  # 5分钟
        )
        
        # L2: 文件缓存（中等速度）
        self.l2_cache = FileCache(
            cache_dir=PERFORMANCE_CONFIG.get('cache_dir', 'cache'),
            max_size_mb=PERFORMANCE_CONFIG.get('l2_cache_size_mb', 100)
        )
        
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        self.lock = threading.Lock()
    
    @monitor_performance('multilevel_cache_get')
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（多层查找）"""
        with self.lock:
            self.stats['total_requests'] += 1
        
        # L1缓存查找
        value = self.l1_cache.get(key)
        if value is not None:
            with self.lock:
                self.stats['l1_hits'] += 1
            return value
        
        # L2缓存查找
        value = self.l2_cache.get(key)
        if value is not None:
            with self.lock:
                self.stats['l2_hits'] += 1
            
            # 提升到L1缓存
            self.l1_cache.set(key, value)
            return value
        
        # 缓存未命中
        with self.lock:
            self.stats['misses'] += 1
        
        return None
    
    @monitor_performance('multilevel_cache_set')
    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存值（写入所有层）"""
        if ttl is None:
            ttl = PERFORMANCE_CONFIG.get('cache_ttl', 3600)
        
        # 写入L1缓存
        self.l1_cache.set(key, value)
        
        # 写入L2缓存
        self.l2_cache.set(key, value, ttl)
    
    def clear(self):
        """清空所有缓存层"""
        self.l1_cache.clear()
        self.l2_cache.clear()
        
        with self.lock:
            self.stats = {
                'l1_hits': 0,
                'l2_hits': 0,
                'misses': 0,
                'total_requests': 0
            }
    
    def get_stats(self) -> Dict:
        """获取多层缓存统计信息"""
        with self.lock:
            total_requests = self.stats['total_requests']
            if total_requests > 0:
                l1_hit_rate = self.stats['l1_hits'] / total_requests
                l2_hit_rate = self.stats['l2_hits'] / total_requests
                overall_hit_rate = (self.stats['l1_hits'] + self.stats['l2_hits']) / total_requests
            else:
                l1_hit_rate = l2_hit_rate = overall_hit_rate = 0
            
            return {
                'l1_cache': self.l1_cache.get_stats(),
                'l2_cache': self.l2_cache.get_stats(),
                'performance': {
                    'total_requests': total_requests,
                    'l1_hits': self.stats['l1_hits'],
                    'l2_hits': self.stats['l2_hits'],
                    'misses': self.stats['misses'],
                    'l1_hit_rate': f"{l1_hit_rate:.2%}",
                    'l2_hit_rate': f"{l2_hit_rate:.2%}",
                    'overall_hit_rate': f"{overall_hit_rate:.2%}"
                }
            }


# 全局多层缓存实例
advanced_cache = MultiLevelCache()


def advanced_cached(ttl: Optional[int] = None, key_prefix: str = "", use_multilevel: bool = True):
    """
    高级缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
        use_multilevel: 是否使用多层缓存
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if not PERFORMANCE_CONFIG.get('cache_enabled', True):
                return func(*args, **kwargs)
            
            # 生成缓存键
            import hashlib
            import json
            
            key_data = {
                'func': f"{func.__module__}.{func.__name__}",
                'args': args,
                'kwargs': sorted(kwargs.items()) if kwargs else {}
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            cache_key = f"{key_prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
            
            # 尝试从缓存获取
            if use_multilevel:
                cached_result = advanced_cache.get(cache_key)
            else:
                from utils.cache_manager import _global_cache
                cached_result = _global_cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            
            if use_multilevel:
                advanced_cache.set(cache_key, result, ttl)
            else:
                from utils.cache_manager import _global_cache
                _global_cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator
