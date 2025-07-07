"""
CSV数据处理优化模块 - 提供高性能的CSV读写和处理功能
"""
import pandas as pd
import numpy as np
import os
import time
import gc
from typing import List, Dict, Any, Optional, Iterator
from functools import lru_cache
from utils.cache_manager import cached, get_cached_csv_data, cache_csv_data
from config.settings import PERFORMANCE_CONFIG


class CSVOptimizer:
    """CSV数据处理优化器"""
    
    def __init__(self, batch_size: int = None):
        self.batch_size = batch_size or PERFORMANCE_CONFIG.get('batch_size', 100)
        self.memory_limit_mb = PERFORMANCE_CONFIG.get('memory_limit_mb', 512)
    
    @cached(ttl=1800, key_prefix="csv_read")
    def read_csv_optimized(self, csv_path: str, **kwargs) -> pd.DataFrame:
        """
        优化的CSV读取函数
        
        Args:
            csv_path: CSV文件路径
            **kwargs: pandas.read_csv的其他参数
            
        Returns:
            pd.DataFrame: 读取的数据
        """
        if not os.path.exists(csv_path):
            print(f"警告: CSV文件不存在: {csv_path}")
            return pd.DataFrame()
        
        try:
            # 检查缓存
            cached_data = get_cached_csv_data(csv_path)
            if cached_data is not None:
                print(f"从缓存加载CSV数据: {csv_path}")
                return cached_data
            
            # 获取文件大小
            file_size_mb = os.path.getsize(csv_path) / 1024 / 1024
            print(f"读取CSV文件: {csv_path} (大小: {file_size_mb:.2f}MB)")
            
            # 根据文件大小选择读取策略
            if file_size_mb > self.memory_limit_mb:
                print("文件较大，使用分块读取")
                return self._read_large_csv(csv_path, **kwargs)
            else:
                # 优化数据类型
                df = pd.read_csv(csv_path, **kwargs)
                df = self._optimize_dtypes(df)
                
                # 缓存数据
                cache_csv_data(csv_path, df)
                print(f"CSV数据已缓存，形状: {df.shape}")
                
                return df
                
        except Exception as e:
            print(f"读取CSV文件失败: {csv_path}, 错误: {str(e)}")
            return pd.DataFrame()
    
    def _read_large_csv(self, csv_path: str, **kwargs) -> pd.DataFrame:
        """分块读取大型CSV文件"""
        chunks = []
        chunk_size = self.batch_size * 10  # 增大分块大小
        
        try:
            for chunk in pd.read_csv(csv_path, chunksize=chunk_size, **kwargs):
                chunk = self._optimize_dtypes(chunk)
                chunks.append(chunk)
                
                # 内存检查
                if self._check_memory_usage():
                    print("内存使用过高，执行垃圾回收")
                    gc.collect()
            
            if chunks:
                df = pd.concat(chunks, ignore_index=True)
                print(f"分块读取完成，总形状: {df.shape}")
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"分块读取失败: {str(e)}")
            return pd.DataFrame()
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """优化数据类型以节省内存"""
        if df.empty:
            return df
        
        try:
            # 优化数值列
            for col in df.select_dtypes(include=[np.number]).columns:
                if df[col].dtype == 'int64':
                    if df[col].min() >= 0 and df[col].max() <= 65535:
                        df[col] = df[col].astype('uint16')
                    elif df[col].min() >= -32768 and df[col].max() <= 32767:
                        df[col] = df[col].astype('int16')
                    elif df[col].min() >= -2147483648 and df[col].max() <= 2147483647:
                        df[col] = df[col].astype('int32')
                
                elif df[col].dtype == 'float64':
                    df[col] = pd.to_numeric(df[col], downcast='float')
            
            # 优化字符串列
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].nunique() / len(df) < 0.5:  # 如果唯一值比例小于50%，转换为category
                    df[col] = df[col].astype('category')
            
            return df
            
        except Exception as e:
            print(f"数据类型优化失败: {str(e)}")
            return df
    
    def write_csv_optimized(self, df: pd.DataFrame, csv_path: str, **kwargs):
        """
        优化的CSV写入函数
        
        Args:
            df: 要写入的DataFrame
            csv_path: 输出文件路径
            **kwargs: pandas.to_csv的其他参数
        """
        if df.empty:
            print("警告: DataFrame为空，跳过写入")
            return
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # 默认参数
            default_kwargs = {
                'index': False,
                'encoding': 'utf-8-sig'
            }
            default_kwargs.update(kwargs)
            
            # 根据数据大小选择写入策略
            if len(df) > self.batch_size * 10:
                print(f"数据量较大({len(df)}行)，使用分批写入")
                self._write_large_csv(df, csv_path, **default_kwargs)
            else:
                df.to_csv(csv_path, **default_kwargs)
                print(f"CSV文件已保存: {csv_path} (形状: {df.shape})")
            
            # 更新缓存
            cache_csv_data(csv_path, df)
            
        except Exception as e:
            print(f"写入CSV文件失败: {csv_path}, 错误: {str(e)}")
    
    def _write_large_csv(self, df: pd.DataFrame, csv_path: str, **kwargs):
        """分批写入大型DataFrame"""
        try:
            # 第一批写入（包含表头）
            first_batch = df.iloc[:self.batch_size]
            first_batch.to_csv(csv_path, **kwargs)
            
            # 后续批次追加写入（不包含表头）
            kwargs['header'] = False
            kwargs['mode'] = 'a'
            
            for i in range(self.batch_size, len(df), self.batch_size):
                batch = df.iloc[i:i + self.batch_size]
                batch.to_csv(csv_path, **kwargs)
                
                # 内存检查
                if i % (self.batch_size * 5) == 0:
                    if self._check_memory_usage():
                        gc.collect()
            
            print(f"分批写入完成: {csv_path} (总行数: {len(df)})")
            
        except Exception as e:
            print(f"分批写入失败: {str(e)}")
    
    def batch_process_data(self, data: List[Dict], process_func: callable) -> List[Any]:
        """
        批量处理数据
        
        Args:
            data: 要处理的数据列表
            process_func: 处理函数
            
        Returns:
            List[Any]: 处理结果列表
        """
        results = []
        total_batches = (len(data) + self.batch_size - 1) // self.batch_size
        
        print(f"开始批量处理，总数据量: {len(data)}, 批次大小: {self.batch_size}, 总批次: {total_batches}")
        
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            try:
                print(f"处理批次 {batch_num}/{total_batches}")
                batch_results = process_func(batch)
                results.extend(batch_results if isinstance(batch_results, list) else [batch_results])
                
                # 内存检查
                if batch_num % 5 == 0:
                    if self._check_memory_usage():
                        print("执行内存清理")
                        gc.collect()
                        
            except Exception as e:
                print(f"批次 {batch_num} 处理失败: {str(e)}")
                continue
        
        print(f"批量处理完成，结果数量: {len(results)}")
        return results
    
    def _check_memory_usage(self) -> bool:
        """检查内存使用情况"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            return memory_percent > 80  # 内存使用超过80%时返回True
        except ImportError:
            return False
    
    @staticmethod
    def merge_csv_files(file_paths: List[str], output_path: str, remove_duplicates: bool = True):
        """
        合并多个CSV文件
        
        Args:
            file_paths: CSV文件路径列表
            output_path: 输出文件路径
            remove_duplicates: 是否去重
        """
        optimizer = CSVOptimizer()
        dfs = []
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                df = optimizer.read_csv_optimized(file_path)
                if not df.empty:
                    dfs.append(df)
        
        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            
            if remove_duplicates and not merged_df.empty:
                original_len = len(merged_df)
                merged_df = merged_df.drop_duplicates()
                print(f"去重完成: {original_len} -> {len(merged_df)}")
            
            optimizer.write_csv_optimized(merged_df, output_path)
            print(f"文件合并完成: {output_path}")
        else:
            print("没有有效的CSV文件可合并")


# 全局优化器实例
csv_optimizer = CSVOptimizer()
