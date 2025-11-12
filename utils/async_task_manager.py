"""
异步任务管理器 - 处理爬虫和数据处理的异步任务
"""
import asyncio
import aiohttp
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional
import traceback
from datetime import datetime
from utils.performance_monitor import monitor_performance, performance_monitor
from utils.cache_manager import cached, memory_cleanup
from config.settings import PERFORMANCE_CONFIG


class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, max_workers: int = None, max_concurrent_requests: int = 10):
        self.max_workers = max_workers or PERFORMANCE_CONFIG.get('max_workers', 4)
        self.max_concurrent_requests = max_concurrent_requests
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.task_queue = queue.Queue()
        self.results = {}
        self.running_tasks = {}
        self.lock = threading.Lock()
        
        # 网络请求会话
        self.session = None
        self._session_lock = threading.Lock()
    
    async def get_session(self):
        """获取异步HTTP会话"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent_requests,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=20
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
                }
            )
        
        return self.session
    
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    @monitor_performance('async_http_request')
    async def async_http_request(self, url: str, params: Dict = None, headers: Dict = None, 
                                method: str = 'GET', **kwargs) -> Optional[Dict]:
        """
        异步HTTP请求
        
        Args:
            url: 请求URL
            params: 请求参数
            headers: 请求头
            method: 请求方法
            **kwargs: 其他参数
            
        Returns:
            响应数据或None
        """
        session = await self.get_session()
        
        try:
            # 合并请求头
            request_headers = session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            async with session.request(
                method=method,
                url=url,
                params=params,
                headers=request_headers,
                **kwargs
            ) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        try:
                            import json
                            return json.loads(text)
                        except:
                            return {'text': text}
                else:
                    print(f"HTTP请求失败: {url}, 状态码: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            print(f"请求超时: {url}")
            return None
        except Exception as e:
            print(f"请求异常: {url}, 错误: {str(e)}")
            return None
    
    async def batch_http_requests(self, requests: List[Dict]) -> List[Optional[Dict]]:
        """
        批量异步HTTP请求
        
        Args:
            requests: 请求列表，每个元素包含url和其他参数
            
        Returns:
            响应结果列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def limited_request(request_info):
            async with semaphore:
                return await self.async_http_request(**request_info)
        
        tasks = [limited_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"批量请求异常: {str(result)}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def submit_task(self, func: Callable, *args, task_id: str = None, **kwargs) -> str:
        """
        提交异步任务
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            task_id: 任务ID，如果不提供则自动生成
            **kwargs: 函数关键字参数
            
        Returns:
            任务ID
        """
        if task_id is None:
            task_id = f"task_{int(time.time() * 1000)}_{id(func)}"
        
        with self.lock:
            if task_id in self.running_tasks:
                print(f"任务 {task_id} 已存在")
                return task_id
            
            future = self.executor.submit(self._execute_task, func, task_id, *args, **kwargs)
            self.running_tasks[task_id] = {
                'future': future,
                'start_time': time.time(),
                'status': 'running'
            }
        
        print(f"任务 {task_id} 已提交")
        return task_id
    
    def _execute_task(self, func: Callable, task_id: str, *args, **kwargs):
        """执行任务的内部方法"""
        try:
            print(f"开始执行任务: {task_id}")
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            print(f"任务 {task_id} 执行完成，耗时: {execution_time:.2f}秒")
            
            with self.lock:
                self.results[task_id] = {
                    'result': result,
                    'status': 'completed',
                    'execution_time': execution_time,
                    'completed_at': datetime.now().isoformat()
                }
                
                if task_id in self.running_tasks:
                    self.running_tasks[task_id]['status'] = 'completed'
            
            return result
            
        except Exception as e:
            error_msg = f"任务 {task_id} 执行失败: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            
            with self.lock:
                self.results[task_id] = {
                    'error': error_msg,
                    'status': 'failed',
                    'failed_at': datetime.now().isoformat()
                }
                
                if task_id in self.running_tasks:
                    self.running_tasks[task_id]['status'] = 'failed'
            
            raise
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        with self.lock:
            if task_id in self.running_tasks:
                task_info = self.running_tasks[task_id].copy()
                
                # 检查是否完成
                if task_info['future'].done():
                    try:
                        task_info['future'].result()  # 获取结果或异常
                    except Exception:
                        pass  # 异常已在_execute_task中处理
                
                # 添加结果信息
                if task_id in self.results:
                    task_info.update(self.results[task_id])
                
                return task_info
            
            elif task_id in self.results:
                return self.results[task_id]
            
            else:
                return {'status': 'not_found'}
    
    def get_task_result(self, task_id: str, timeout: float = None) -> Any:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            
        Returns:
            任务结果
        """
        with self.lock:
            if task_id in self.running_tasks:
                future = self.running_tasks[task_id]['future']
                
                try:
                    result = future.result(timeout=timeout)
                    return result
                except Exception as e:
                    print(f"获取任务结果失败: {task_id}, 错误: {str(e)}")
                    raise
            
            elif task_id in self.results:
                result_info = self.results[task_id]
                if 'result' in result_info:
                    return result_info['result']
                elif 'error' in result_info:
                    raise Exception(result_info['error'])
            
            raise ValueError(f"任务不存在: {task_id}")
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.lock:
            if task_id in self.running_tasks:
                future = self.running_tasks[task_id]['future']
                if future.cancel():
                    self.running_tasks[task_id]['status'] = 'cancelled'
                    print(f"任务 {task_id} 已取消")
                    return True
                else:
                    print(f"任务 {task_id} 无法取消（可能已开始执行）")
                    return False
            
            return False
    
    def get_all_tasks(self) -> Dict:
        """获取所有任务状态"""
        with self.lock:
            all_tasks = {}
            
            # 运行中的任务
            for task_id, task_info in self.running_tasks.items():
                status_info = task_info.copy()
                if task_id in self.results:
                    status_info.update(self.results[task_id])
                all_tasks[task_id] = status_info
            
            # 已完成的任务（不在running_tasks中的）
            for task_id, result_info in self.results.items():
                if task_id not in all_tasks:
                    all_tasks[task_id] = result_info
            
            return all_tasks
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的任务"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self.lock:
            # 清理已完成的任务
            completed_tasks = []
            for task_id, task_info in self.running_tasks.items():
                if (task_info['status'] in ['completed', 'failed', 'cancelled'] and
                    current_time - task_info['start_time'] > max_age_seconds):
                    completed_tasks.append(task_id)
            
            for task_id in completed_tasks:
                self.running_tasks.pop(task_id, None)
                self.results.pop(task_id, None)
            
            if completed_tasks:
                print(f"清理了 {len(completed_tasks)} 个已完成的任务")
    
    def shutdown(self):
        """关闭任务管理器"""
        print("正在关闭异步任务管理器...")
        
        # 等待所有任务完成
        with self.lock:
            futures = [task_info['future'] for task_info in self.running_tasks.values()]
        
        for future in futures:
            try:
                future.result(timeout=5)  # 等待最多5秒
            except Exception:
                pass
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        # 清理资源
        asyncio.create_task(self.close_session())
        
        print("异步任务管理器已关闭")


# 全局任务管理器实例
task_manager = AsyncTaskManager()
