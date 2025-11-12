"""
数据流水线优化器 - 提供高效的数据处理流水线
"""
import pandas as pd
import numpy as np
import time
import gc
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from utils.performance_monitor import monitor_performance, performance_monitor
from utils.cache_manager import cached, memory_cleanup
from utils.csv_optimizer import csv_optimizer
from config.settings import PERFORMANCE_CONFIG


class DataPipeline:
    """数据处理流水线"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or PERFORMANCE_CONFIG.get('max_workers', 4)
        self.steps = []
        self.results = {}
        self.stats = {
            'total_processed': 0,
            'total_time': 0,
            'step_times': {},
            'memory_usage': []
        }
    
    def add_step(self, name: str, func: Callable, **kwargs):
        """
        添加处理步骤
        
        Args:
            name: 步骤名称
            func: 处理函数
            **kwargs: 函数参数
        """
        self.steps.append({
            'name': name,
            'func': func,
            'kwargs': kwargs
        })
        return self
    
    @monitor_performance('data_pipeline_execute')
    def execute(self, data: Any, parallel: bool = True) -> Any:
        """
        执行数据流水线
        
        Args:
            data: 输入数据
            parallel: 是否并行处理
            
        Returns:
            处理后的数据
        """
        start_time = time.time()
        current_data = data
        
        print(f"开始执行数据流水线，步骤数: {len(self.steps)}")
        
        for i, step in enumerate(self.steps):
            step_start = time.time()
            step_name = step['name']
            
            try:
                print(f"执行步骤 {i+1}/{len(self.steps)}: {step_name}")
                
                # 记录内存使用
                memory_before = self._get_memory_usage()
                
                # 执行步骤
                if parallel and hasattr(step['func'], '__parallel__'):
                    current_data = self._execute_parallel_step(step, current_data)
                else:
                    current_data = step['func'](current_data, **step['kwargs'])
                
                # 记录内存使用
                memory_after = self._get_memory_usage()
                
                step_time = time.time() - step_start
                self.stats['step_times'][step_name] = step_time
                self.stats['memory_usage'].append({
                    'step': step_name,
                    'before_mb': memory_before,
                    'after_mb': memory_after,
                    'delta_mb': memory_after - memory_before
                })
                
                print(f"步骤 {step_name} 完成，耗时: {step_time:.2f}秒")
                
                # 定期内存清理
                if i % 3 == 0:
                    gc.collect()
                    
            except Exception as e:
                print(f"步骤 {step_name} 执行失败: {str(e)}")
                raise
        
        total_time = time.time() - start_time
        self.stats['total_time'] = total_time
        self.stats['total_processed'] += 1
        
        print(f"数据流水线执行完成，总耗时: {total_time:.2f}秒")
        return current_data
    
    def _execute_parallel_step(self, step, data):
        """执行并行步骤"""
        func = step['func']
        kwargs = step['kwargs']
        
        if isinstance(data, (list, tuple)):
            # 列表数据并行处理
            return self._parallel_process_list(func, data, **kwargs)
        elif isinstance(data, pd.DataFrame):
            # DataFrame分块并行处理
            return self._parallel_process_dataframe(func, data, **kwargs)
        else:
            # 单个数据项
            return func(data, **kwargs)
    
    def _parallel_process_list(self, func: Callable, data_list: List, **kwargs) -> List:
        """并行处理列表数据"""
        chunk_size = max(1, len(data_list) // self.max_workers)
        chunks = [data_list[i:i + chunk_size] for i in range(0, len(data_list), chunk_size)]
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_chunk = {
                executor.submit(func, chunk, **kwargs): chunk 
                for chunk in chunks
            }
            
            for future in as_completed(future_to_chunk):
                try:
                    result = future.result()
                    if isinstance(result, list):
                        results.extend(result)
                    else:
                        results.append(result)
                except Exception as e:
                    print(f"并行处理失败: {str(e)}")
        
        return results
    
    def _parallel_process_dataframe(self, func: Callable, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """并行处理DataFrame"""
        chunk_size = max(1, len(df) // self.max_workers)
        chunks = [df.iloc[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_chunk = {
                executor.submit(func, chunk, **kwargs): chunk 
                for chunk in chunks
            }
            
            for future in as_completed(future_to_chunk):
                try:
                    result = future.result()
                    if isinstance(result, pd.DataFrame):
                        results.append(result)
                except Exception as e:
                    print(f"DataFrame并行处理失败: {str(e)}")
        
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return df
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def get_stats(self) -> Dict:
        """获取流水线统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_processed': 0,
            'total_time': 0,
            'step_times': {},
            'memory_usage': []
        }
    
    def clear(self):
        """清空流水线步骤"""
        self.steps.clear()
        self.reset_stats()


# 预定义的数据处理函数

def parallel_sentiment_analysis(data_chunk: List[str], **kwargs) -> List[str]:
    """并行情感分析函数"""
    from model.nlp import batch_analyze_sentiment
    return batch_analyze_sentiment(data_chunk)

# 标记为并行函数
parallel_sentiment_analysis.__parallel__ = True


def parallel_text_cleaning(data_chunk: List[str], **kwargs) -> List[str]:
    """并行文本清理函数"""
    from model.ciyuntu import clean_text
    
    cleaned_texts = []
    for text in data_chunk:
        cleaned = clean_text(text)
        cleaned_texts.append(cleaned)
    
    return cleaned_texts

# 标记为并行函数
parallel_text_cleaning.__parallel__ = True


def parallel_data_validation(df_chunk: pd.DataFrame, required_columns: List[str] = None, **kwargs) -> pd.DataFrame:
    """并行数据验证函数"""
    if required_columns:
        # 确保必需列存在
        for col in required_columns:
            if col not in df_chunk.columns:
                df_chunk[col] = 'N/A'
    
    # 数据类型优化
    return csv_optimizer._optimize_dtypes(csv_optimizer, df_chunk)

# 标记为并行函数
parallel_data_validation.__parallel__ = True


class CrawlerPipeline(DataPipeline):
    """爬虫数据处理流水线"""
    
    def __init__(self, max_workers: int = None):
        super().__init__(max_workers)
        self._setup_crawler_pipeline()
    
    def _setup_crawler_pipeline(self):
        """设置爬虫数据处理流水线"""
        self.add_step('数据验证', self._validate_crawler_data)
        self.add_step('数据清理', self._clean_crawler_data)
        self.add_step('数据去重', self._deduplicate_data)
        self.add_step('数据标准化', self._normalize_data)
    
    def _validate_crawler_data(self, data: List[Dict], **kwargs) -> List[Dict]:
        """验证爬虫数据"""
        valid_data = []
        for item in data:
            if isinstance(item, dict) and item:
                # 基本验证
                if any(key in item for key in ['微博内容', '视频描述', '内容']):
                    valid_data.append(item)
        
        print(f"数据验证完成: {len(data)} -> {len(valid_data)}")
        return valid_data
    
    def _clean_crawler_data(self, data: List[Dict], **kwargs) -> List[Dict]:
        """清理爬虫数据"""
        cleaned_data = []
        for item in data:
            cleaned_item = item.copy()
            
            # 清理文本内容
            for key in ['微博内容', '视频描述', '内容']:
                if key in cleaned_item and cleaned_item[key]:
                    from model.ciyuntu import clean_text
                    cleaned_item[key] = clean_text(str(cleaned_item[key]))
            
            # 标准化数值字段
            for key in ['转发数', '评论数', '点赞数', '收藏数', '分享数']:
                if key in cleaned_item:
                    try:
                        cleaned_item[key] = int(cleaned_item[key]) if cleaned_item[key] else 0
                    except (ValueError, TypeError):
                        cleaned_item[key] = 0
            
            cleaned_data.append(cleaned_item)
        
        print(f"数据清理完成: {len(cleaned_data)} 条记录")
        return cleaned_data
    
    def _deduplicate_data(self, data: List[Dict], **kwargs) -> List[Dict]:
        """数据去重"""
        seen_ids = set()
        unique_data = []
        
        for item in data:
            # 尝试多个可能的ID字段
            item_id = None
            for id_field in ['微博id', 'uni_id', 'id', 'bid']:
                if id_field in item and item[id_field]:
                    item_id = item[id_field]
                    break
            
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_data.append(item)
            elif not item_id:
                # 如果没有ID，基于内容去重
                content = item.get('微博内容') or item.get('视频描述') or item.get('内容', '')
                content_hash = hash(content[:100])  # 使用内容前100字符的哈希
                if content_hash not in seen_ids:
                    seen_ids.add(content_hash)
                    unique_data.append(item)
        
        print(f"数据去重完成: {len(data)} -> {len(unique_data)}")
        return unique_data
    
    def _normalize_data(self, data: List[Dict], **kwargs) -> pd.DataFrame:
        """数据标准化"""
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # 标准化时间格式
        for time_col in ['发布时间', '创建时间', 'created_at']:
            if time_col in df.columns:
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        
        # 数据类型优化
        df = csv_optimizer._optimize_dtypes(csv_optimizer, df)
        
        print(f"数据标准化完成: {df.shape}")
        return df


# 全局流水线实例
crawler_pipeline = CrawlerPipeline()
data_pipeline = DataPipeline()
