"""
智能数据预处理模块 - 高级数据清洗和预处理
"""
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.performance_monitor import monitor_performance
from utils.advanced_cache import advanced_cached
from config.settings import PERFORMANCE_CONFIG


class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        # 编译正则表达式以提高性能
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.mention_pattern = re.compile(r'@[a-zA-Z0-9_\u4e00-\u9fff]+')
        self.hashtag_pattern = re.compile(r'#[^#\s]+#?')
        self.emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+')
        self.whitespace_pattern = re.compile(r'\s+')
        self.punctuation_pattern = re.compile(r'[^\w\s\u4e00-\u9fff]')
        
        # 停用词列表
        self.stopwords = self._load_stopwords()
    
    def _load_stopwords(self) -> set:
        """加载停用词"""
        # 基础中文停用词
        basic_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '里', '就是', '还是', '为了', '还有', '可以', '这个',
            '但是', '如果', '只是', '或者', '因为', '所以', '虽然', '然后', '而且', '不过'
        }
        
        # 可以从文件加载更多停用词
        try:
            stopwords_file = PERFORMANCE_CONFIG.get('stopwords_file', '')
            if stopwords_file:
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    file_stopwords = set(line.strip() for line in f if line.strip())
                basic_stopwords.update(file_stopwords)
        except Exception as e:
            print(f"加载停用词文件失败: {str(e)}")
        
        return basic_stopwords
    
    @advanced_cached(ttl=1800, key_prefix="text_clean")
    def clean_text(self, text: str, remove_urls: bool = True, remove_mentions: bool = True,
                   remove_hashtags: bool = False, remove_emojis: bool = False,
                   normalize_whitespace: bool = True) -> str:
        """
        清洗文本
        
        Args:
            text: 原始文本
            remove_urls: 是否移除URL
            remove_mentions: 是否移除@提及
            remove_hashtags: 是否移除话题标签
            remove_emojis: 是否移除表情符号
            normalize_whitespace: 是否标准化空白字符
            
        Returns:
            清洗后的文本
        """
        if not isinstance(text, str) or not text.strip():
            return ""
        
        cleaned_text = text
        
        # 移除URL
        if remove_urls:
            cleaned_text = self.url_pattern.sub('', cleaned_text)
        
        # 移除@提及
        if remove_mentions:
            cleaned_text = self.mention_pattern.sub('', cleaned_text)
        
        # 移除话题标签
        if remove_hashtags:
            cleaned_text = self.hashtag_pattern.sub('', cleaned_text)
        
        # 移除表情符号
        if remove_emojis:
            cleaned_text = self.emoji_pattern.sub('', cleaned_text)
        
        # 标准化空白字符
        if normalize_whitespace:
            cleaned_text = self.whitespace_pattern.sub(' ', cleaned_text)
        
        return cleaned_text.strip()
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本内容
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 简单的关键词提取（基于词频）
        # 实际项目中可以使用更复杂的算法如TF-IDF
        words = text.split()
        
        # 过滤停用词和短词
        filtered_words = [
            word for word in words 
            if len(word) > 1 and word not in self.stopwords
        ]
        
        # 统计词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序并返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def batch_clean_texts(self, texts: List[str], **kwargs) -> List[str]:
        """
        批量清洗文本
        
        Args:
            texts: 文本列表
            **kwargs: clean_text的参数
            
        Returns:
            清洗后的文本列表
        """
        if not texts:
            return []
        
        # 使用线程池并行处理
        max_workers = min(len(texts), PERFORMANCE_CONFIG.get('max_workers', 4))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.clean_text, text, **kwargs) for text in texts]
            results = []
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"文本清洗失败: {str(e)}")
                    results.append("")
        
        return results


class DataValidator:
    """数据验证器"""
    
    def __init__(self):
        self.validation_rules = {}
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认验证规则"""
        self.validation_rules = {
            'weibo': {
                'required_fields': ['微博内容', '发布时间'],
                'numeric_fields': ['转发数', '评论数', '点赞数'],
                'text_fields': ['微博内容', '微博作者'],
                'max_content_length': 5000,
                'min_content_length': 1
            },
            'douyin': {
                'required_fields': ['视频描述', '发布时间'],
                'numeric_fields': ['点赞数', '评论数', '收藏数', '分享数'],
                'text_fields': ['视频描述', '用户名'],
                'max_content_length': 3000,
                'min_content_length': 1
            }
        }
    
    @monitor_performance('data_validation')
    def validate_record(self, record: Dict, data_type: str = 'weibo') -> Dict:
        """
        验证单条记录
        
        Args:
            record: 数据记录
            data_type: 数据类型
            
        Returns:
            验证结果字典
        """
        if data_type not in self.validation_rules:
            return {'valid': False, 'errors': [f'未知数据类型: {data_type}']}
        
        rules = self.validation_rules[data_type]
        errors = []
        warnings = []
        
        # 检查必需字段
        for field in rules['required_fields']:
            if field not in record or not record[field]:
                errors.append(f'缺少必需字段: {field}')
        
        # 检查数值字段
        for field in rules['numeric_fields']:
            if field in record:
                try:
                    value = record[field]
                    if value is not None and value != '':
                        float_value = float(value)
                        if float_value < 0:
                            warnings.append(f'数值字段 {field} 为负数: {float_value}')
                except (ValueError, TypeError):
                    errors.append(f'数值字段 {field} 格式错误: {record[field]}')
        
        # 检查文本字段长度
        content_field = rules['text_fields'][0] if rules['text_fields'] else None
        if content_field and content_field in record:
            content = str(record[content_field])
            if len(content) > rules['max_content_length']:
                warnings.append(f'内容过长: {len(content)} > {rules["max_content_length"]}')
            elif len(content) < rules['min_content_length']:
                errors.append(f'内容过短: {len(content)} < {rules["min_content_length"]}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_batch(self, records: List[Dict], data_type: str = 'weibo') -> Dict:
        """
        批量验证记录
        
        Args:
            records: 记录列表
            data_type: 数据类型
            
        Returns:
            批量验证结果
        """
        if not records:
            return {'valid_count': 0, 'invalid_count': 0, 'warning_count': 0, 'details': []}
        
        valid_count = 0
        invalid_count = 0
        warning_count = 0
        details = []
        
        # 使用线程池并行验证
        max_workers = min(len(records), PERFORMANCE_CONFIG.get('max_workers', 4))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.validate_record, record, data_type) 
                for record in records
            ]
            
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    
                    if result['valid']:
                        valid_count += 1
                    else:
                        invalid_count += 1
                    
                    if result['warnings']:
                        warning_count += 1
                    
                    if result['errors'] or result['warnings']:
                        details.append({
                            'index': i,
                            'errors': result['errors'],
                            'warnings': result['warnings']
                        })
                        
                except Exception as e:
                    invalid_count += 1
                    details.append({
                        'index': i,
                        'errors': [f'验证异常: {str(e)}'],
                        'warnings': []
                    })
        
        return {
            'total_count': len(records),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'warning_count': warning_count,
            'success_rate': valid_count / len(records) * 100,
            'details': details[:50]  # 限制详情数量
        }


class SmartPreprocessor:
    """智能预处理器"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.data_validator = DataValidator()
        self.stats = {
            'processed_records': 0,
            'cleaned_texts': 0,
            'validation_errors': 0,
            'processing_time': 0
        }
    
    @monitor_performance('smart_preprocessing')
    def preprocess_data(self, data: List[Dict], data_type: str = 'weibo',
                       clean_text: bool = True, validate_data: bool = True) -> Dict:
        """
        智能预处理数据
        
        Args:
            data: 原始数据列表
            data_type: 数据类型
            clean_text: 是否清洗文本
            validate_data: 是否验证数据
            
        Returns:
            预处理结果
        """
        import time
        start_time = time.time()
        
        if not data:
            return {'processed_data': [], 'stats': self.stats}
        
        processed_data = data.copy()
        
        # 数据验证
        validation_result = None
        if validate_data:
            validation_result = self.data_validator.validate_batch(processed_data, data_type)
            self.stats['validation_errors'] += validation_result['invalid_count']
        
        # 文本清洗
        if clean_text:
            content_field = self._get_content_field(data_type)
            if content_field:
                texts = [record.get(content_field, '') for record in processed_data]
                cleaned_texts = self.text_processor.batch_clean_texts(texts)
                
                for i, cleaned_text in enumerate(cleaned_texts):
                    if i < len(processed_data):
                        processed_data[i][content_field] = cleaned_text
                
                self.stats['cleaned_texts'] += len(cleaned_texts)
        
        # 更新统计
        self.stats['processed_records'] += len(processed_data)
        self.stats['processing_time'] += time.time() - start_time
        
        return {
            'processed_data': processed_data,
            'validation_result': validation_result,
            'stats': self.stats.copy()
        }
    
    def _get_content_field(self, data_type: str) -> Optional[str]:
        """获取内容字段名"""
        field_mapping = {
            'weibo': '微博内容',
            'douyin': '视频描述'
        }
        return field_mapping.get(data_type)
    
    def get_stats(self) -> Dict:
        """获取预处理统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'processed_records': 0,
            'cleaned_texts': 0,
            'validation_errors': 0,
            'processing_time': 0
        }


# 全局实例
smart_preprocessor = SmartPreprocessor()
