"""
性能监控模块 - 监控系统性能指标和资源使用情况
"""
import time
import psutil
import os
import threading
import json
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional, Callable
from utils.cache_manager import get_cache_stats
from config.settings import PERFORMANCE_CONFIG


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = []
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.process = psutil.Process(os.getpid())
    
    def get_system_metrics(self) -> Dict:
        """获取系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            process_memory = self.process.memory_info()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络统计
            network = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                'memory': {
                    'total_mb': memory.total / 1024 / 1024,
                    'available_mb': memory.available / 1024 / 1024,
                    'percent': memory.percent,
                    'process_rss_mb': process_memory.rss / 1024 / 1024,
                    'process_vms_mb': process_memory.vms / 1024 / 1024
                },
                'disk': {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'used_gb': disk.used / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'cache': get_cache_stats(),
                'uptime_seconds': time.time() - self.start_time
            }
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def record_metric(self, metric_name: str, value: float, tags: Optional[Dict] = None):
        """记录性能指标"""
        with self.lock:
            metric = {
                'timestamp': datetime.now().isoformat(),
                'name': metric_name,
                'value': value,
                'tags': tags or {}
            }
            self.metrics.append(metric)
            
            # 限制指标数量，避免内存泄漏
            max_metrics = PERFORMANCE_CONFIG.get('max_metrics', 1000)
            if len(self.metrics) > max_metrics:
                self.metrics = self.metrics[-max_metrics:]
    
    def get_metrics_summary(self, metric_name: Optional[str] = None) -> Dict:
        """获取指标摘要"""
        with self.lock:
            if not self.metrics:
                return {}
            
            filtered_metrics = self.metrics
            if metric_name:
                filtered_metrics = [m for m in self.metrics if m['name'] == metric_name]
            
            if not filtered_metrics:
                return {}
            
            values = [m['value'] for m in filtered_metrics]
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'latest': values[-1],
                'first_timestamp': filtered_metrics[0]['timestamp'],
                'latest_timestamp': filtered_metrics[-1]['timestamp']
            }
    
    def clear_metrics(self):
        """清空指标"""
        with self.lock:
            self.metrics.clear()
    
    def export_metrics(self, file_path: str):
        """导出指标到文件"""
        with self.lock:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.metrics, f, ensure_ascii=False, indent=2)
                print(f"指标已导出到: {file_path}")
            except Exception as e:
                print(f"导出指标失败: {str(e)}")


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def monitor_performance(metric_name: str = None, tags: Dict = None):
    """
    性能监控装饰器
    
    Args:
        metric_name: 指标名称，默认使用函数名
        tags: 标签字典
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
                raise
            finally:
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss
                
                execution_time = end_time - start_time
                memory_delta = end_memory - start_memory
                
                # 记录性能指标
                name = metric_name or f"{func.__module__}.{func.__name__}"
                metric_tags = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'success': success,
                    **(tags or {})
                }
                
                if error:
                    metric_tags['error'] = error
                
                performance_monitor.record_metric(f"{name}.execution_time", execution_time, metric_tags)
                performance_monitor.record_metric(f"{name}.memory_delta", memory_delta, metric_tags)
            
            return result
        return wrapper
    return decorator


def get_performance_report() -> Dict:
    """获取性能报告"""
    system_metrics = performance_monitor.get_system_metrics()
    
    # 获取关键指标摘要
    execution_time_summary = performance_monitor.get_metrics_summary('execution_time')
    memory_delta_summary = performance_monitor.get_metrics_summary('memory_delta')
    
    return {
        'system': system_metrics,
        'application': {
            'execution_time': execution_time_summary,
            'memory_delta': memory_delta_summary,
            'total_metrics': len(performance_monitor.metrics)
        },
        'recommendations': _generate_recommendations(system_metrics)
    }


def _generate_recommendations(system_metrics: Dict) -> List[str]:
    """生成性能优化建议"""
    recommendations = []
    
    try:
        # CPU使用率建议
        cpu_percent = system_metrics.get('cpu', {}).get('percent', 0)
        if cpu_percent > 80:
            recommendations.append("CPU使用率过高，建议优化计算密集型操作或增加异步处理")
        
        # 内存使用建议
        memory_percent = system_metrics.get('memory', {}).get('percent', 0)
        if memory_percent > 80:
            recommendations.append("内存使用率过高，建议优化内存使用或增加内存清理")
        
        # 进程内存建议
        process_memory = system_metrics.get('memory', {}).get('process_rss_mb', 0)
        memory_limit = PERFORMANCE_CONFIG.get('memory_limit_mb', 512)
        if process_memory > memory_limit:
            recommendations.append(f"进程内存使用({process_memory:.1f}MB)超过限制({memory_limit}MB)，建议优化内存使用")
        
        # 磁盘使用建议
        disk_percent = system_metrics.get('disk', {}).get('percent', 0)
        if disk_percent > 90:
            recommendations.append("磁盘使用率过高，建议清理临时文件或增加存储空间")
        
        # 缓存建议
        cache_stats = system_metrics.get('cache', {})
        hit_rate = cache_stats.get('hit_rate', 0)
        if hit_rate < 0.5:
            recommendations.append("缓存命中率较低，建议优化缓存策略")
        
        if not recommendations:
            recommendations.append("系统性能良好，无需特别优化")
            
    except Exception as e:
        recommendations.append(f"生成建议时出错: {str(e)}")
    
    return recommendations


def log_performance_metrics():
    """记录性能指标到日志"""
    try:
        report = get_performance_report()
        log_dir = 'logs/performance'
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'performance_{timestamp}.json')
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"性能指标已记录到: {log_file}")
        
    except Exception as e:
        print(f"记录性能指标失败: {str(e)}")


# 定期清理旧指标
def cleanup_old_metrics():
    """清理旧的性能指标"""
    performance_monitor.clear_metrics()
    print("已清理旧的性能指标")
