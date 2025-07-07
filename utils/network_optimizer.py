"""
网络请求优化模块 - 提供高性能的网络请求功能
"""
import requests
import time
import random
from typing import Dict, List, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.cache_manager import cached
from utils.performance_monitor import monitor_performance
from config.settings import PERFORMANCE_CONFIG


class NetworkOptimizer:
    """网络请求优化器"""
    
    def __init__(self):
        self.session = self._create_optimized_session()
        self.request_count = 0
        self.last_request_time = 0
        self.min_interval = 0.1  # 最小请求间隔（秒）
        
        # 用户代理池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
        ]
    
    def _create_optimized_session(self) -> requests.Session:
        """创建优化的请求会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 总重试次数
            backoff_factor=1,  # 退避因子
            status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        # 配置HTTP适配器
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,  # 连接池大小
            pool_maxsize=20,     # 最大连接数
            pool_block=False     # 非阻塞
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认超时
        session.timeout = (10, 30)  # (连接超时, 读取超时)
        
        return session
    
    def _rate_limit(self):
        """请求频率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _get_random_headers(self) -> Dict[str, str]:
        """获取随机请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    @cached(ttl=300, key_prefix="network_request")
    @monitor_performance('network_request')
    def request(self, url: str, method: str = 'GET', params: Dict = None, 
                data: Dict = None, headers: Dict = None, **kwargs) -> Optional[Dict]:
        """
        优化的网络请求
        
        Args:
            url: 请求URL
            method: 请求方法
            params: URL参数
            data: 请求数据
            headers: 请求头
            **kwargs: 其他参数
            
        Returns:
            响应数据或None
        """
        # 频率限制
        self._rate_limit()
        
        # 合并请求头
        request_headers = self._get_random_headers()
        if headers:
            request_headers.update(headers)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=request_headers,
                **kwargs
            )
            
            response.raise_for_status()
            
            # 尝试解析JSON
            try:
                return response.json()
            except ValueError:
                # 如果不是JSON，返回文本
                return {'text': response.text, 'status_code': response.status_code}
                
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {url}, 错误: {str(e)}")
            return None
    
    def batch_request(self, requests_list: List[Dict], max_workers: int = 5) -> List[Optional[Dict]]:
        """
        批量网络请求
        
        Args:
            requests_list: 请求列表
            max_workers: 最大并发数
            
        Returns:
            响应结果列表
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = [None] * len(requests_list)
        
        def make_request(index, request_info):
            try:
                result = self.request(**request_info)
                return index, result
            except Exception as e:
                print(f"批量请求失败: {str(e)}")
                return index, None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(make_request, i, req): i 
                for i, req in enumerate(requests_list)
            }
            
            # 收集结果
            for future in as_completed(future_to_index):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    print(f"批量请求异常: {str(e)}")
        
        return results
    
    def get_stats(self) -> Dict:
        """获取请求统计信息"""
        return {
            'total_requests': self.request_count,
            'session_active': bool(self.session),
            'last_request_time': self.last_request_time,
            'min_interval': self.min_interval
        }
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()


class SpiderOptimizer:
    """爬虫优化器"""
    
    def __init__(self):
        self.network = NetworkOptimizer()
        self.failed_urls = set()
        self.success_count = 0
        self.failure_count = 0
    
    def crawl_page(self, url: str, params: Dict = None, headers: Dict = None, 
                   retry_failed: bool = True) -> Optional[Dict]:
        """
        爬取单个页面
        
        Args:
            url: 页面URL
            params: 请求参数
            headers: 请求头
            retry_failed: 是否重试失败的URL
            
        Returns:
            页面数据或None
        """
        # 检查是否是已知的失败URL
        if not retry_failed and url in self.failed_urls:
            print(f"跳过已知失败URL: {url}")
            return None
        
        result = self.network.request(url, params=params, headers=headers)
        
        if result is not None:
            self.success_count += 1
            # 从失败列表中移除（如果存在）
            self.failed_urls.discard(url)
        else:
            self.failure_count += 1
            self.failed_urls.add(url)
        
        return result
    
    def crawl_pages(self, urls: List[str], params_list: List[Dict] = None, 
                    max_workers: int = 3) -> List[Optional[Dict]]:
        """
        批量爬取页面
        
        Args:
            urls: URL列表
            params_list: 参数列表
            max_workers: 最大并发数
            
        Returns:
            结果列表
        """
        if params_list is None:
            params_list = [{}] * len(urls)
        
        requests_list = []
        for i, url in enumerate(urls):
            params = params_list[i] if i < len(params_list) else {}
            requests_list.append({
                'url': url,
                'params': params
            })
        
        return self.network.batch_request(requests_list, max_workers=max_workers)
    
    def get_stats(self) -> Dict:
        """获取爬虫统计信息"""
        total_requests = self.success_count + self.failure_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': f"{success_rate:.1f}%",
            'failed_urls_count': len(self.failed_urls),
            'network_stats': self.network.get_stats()
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.success_count = 0
        self.failure_count = 0
        self.failed_urls.clear()
    
    def close(self):
        """关闭爬虫优化器"""
        self.network.close()


# 全局实例
network_optimizer = NetworkOptimizer()
spider_optimizer = SpiderOptimizer()


def optimized_spider_request(url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
    """
    优化的爬虫请求函数（兼容现有代码）
    
    Args:
        url: 请求URL
        params: 请求参数
        headers: 请求头
        
    Returns:
        响应数据或None
    """
    return spider_optimizer.crawl_page(url, params=params, headers=headers)


def batch_spider_requests(requests: List[Dict], max_workers: int = 3) -> List[Optional[Dict]]:
    """
    批量爬虫请求函数
    
    Args:
        requests: 请求列表
        max_workers: 最大并发数
        
    Returns:
        响应结果列表
    """
    urls = [req.get('url') for req in requests]
    params_list = [req.get('params', {}) for req in requests]
    
    return spider_optimizer.crawl_pages(urls, params_list, max_workers=max_workers)
