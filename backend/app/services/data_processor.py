"""
数据处理服务
包含多平台数据聚合、风险评估等功能
对应原项目的 nlp.py 和 data_pipeline 功能
"""
import re
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter


class DataProcessor:
    """数据处理器"""
    
    # 统一列名映射
    UNIFIED_COLUMNS = {
        'user_name': {
            'weibo': ['微博作者', 'user_name'],
            'douyin': ['用户名', 'author'],
        },
        'content': {
            'weibo': ['微博内容', 'content'],
            'douyin': ['视频描述', 'title', 'content'],
        },
        'publish_time': {
            'weibo': ['发布时间', 'publish_time'],
            'douyin': ['发布时间', 'publish_time'],
        },
        'like_count': {
            'weibo': ['点赞数', 'like_count'],
            'douyin': ['点赞数', 'like_count'],
        },
        'comment_count': {
            'weibo': ['评论数', 'comment_count'],
            'douyin': ['评论数', 'comment_count'],
        },
        'share_count': {
            'weibo': ['转发数', 'share_count'],
            'douyin': ['分享数', 'share_count'],
        },
        'gender': {
            'weibo': ['性别', 'gender'],
            'douyin': ['性别', 'gender'],
        },
        'province': {
            'weibo': ['省份', 'province'],
            'douyin': ['省份', 'province'],
        },
    }
    
    @staticmethod
    def normalize_gender(value: Any) -> str:
        """标准化性别数据"""
        if not value:
            return '未知'
        value = str(value).lower().strip()
        if value in ['m', '男', 'male', '1']:
            return '男'
        elif value in ['f', '女', 'female', '2']:
            return '女'
        return '未知'
    
    @staticmethod
    def normalize_province(value: Any) -> str:
        """标准化省份数据"""
        if not value or str(value).lower() in ['n/a', 'nan', 'none', '']:
            return '未知'
        return str(value).strip()
    
    def merge_platform_data(
        self,
        weibo_data: List[Dict],
        douyin_data: List[Dict]
    ) -> List[Dict]:
        """
        合并多平台数据
        
        将微博和抖音数据统一格式后合并
        """
        merged = []
        
        # 处理微博数据
        for item in weibo_data:
            unified = {
                'platform': 'weibo',
                'user_name': item.get('user_name', '未知'),
                'content': item.get('content', ''),
                'publish_time': item.get('publish_time'),
                'like_count': item.get('like_count', 0),
                'comment_count': item.get('comment_count', 0),
                'share_count': item.get('share_count', 0),
                'gender': self.normalize_gender(item.get('gender')),
                'province': self.normalize_province(item.get('province')),
                'sentiment_label': item.get('sentiment_label', 'neutral'),
                'sentiment_score': item.get('sentiment_score', 0.5),
                'url': item.get('url', ''),
            }
            merged.append(unified)
        
        # 处理抖音数据
        for item in douyin_data:
            unified = {
                'platform': 'douyin',
                'user_name': item.get('author', '未知'),
                'content': item.get('content') or item.get('title', ''),
                'publish_time': item.get('publish_time'),
                'like_count': item.get('like_count', 0),
                'comment_count': item.get('comment_count', 0),
                'share_count': item.get('share_count', 0),
                'gender': self.normalize_gender(item.get('gender')),
                'province': self.normalize_province(item.get('province')),
                'sentiment_label': item.get('sentiment_label', 'neutral'),
                'sentiment_score': item.get('sentiment_score', 0.5),
                'url': item.get('url', ''),
            }
            merged.append(unified)
        
        return merged
    
    def calculate_statistics(self, data: List[Dict]) -> Dict[str, Any]:
        """
        计算数据统计信息
        
        Returns:
            包含各类统计数据的字典
        """
        if not data:
            return {
                'total_count': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_shares': 0,
                'sentiment_distribution': {},
                'gender_distribution': {},
                'province_distribution': {},
                'platform_distribution': {},
            }
        
        total_likes = sum(d.get('like_count', 0) or 0 for d in data)
        total_comments = sum(d.get('comment_count', 0) or 0 for d in data)
        total_shares = sum(d.get('share_count', 0) or 0 for d in data)
        
        # 情感分布
        sentiment_counter = Counter(d.get('sentiment_label', 'neutral') for d in data)
        
        # 性别分布
        gender_counter = Counter(d.get('gender', '未知') for d in data)
        
        # 省份分布
        province_counter = Counter(d.get('province', '未知') for d in data)
        
        # 平台分布
        platform_counter = Counter(d.get('platform', 'unknown') for d in data)
        
        return {
            'total_count': len(data),
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'total_interaction': total_likes + total_comments + total_shares,
            'sentiment_distribution': dict(sentiment_counter),
            'gender_distribution': dict(gender_counter),
            'province_distribution': dict(province_counter.most_common(20)),
            'platform_distribution': dict(platform_counter),
        }
    
    def calculate_risk_level(self, data: List[Dict]) -> Dict[str, Any]:
        """
        计算风险等级
        
        基于多个维度评估风险：
        1. 情感倾向（负面情感占比）
        2. 传播速度（最近时间段的数据量）
        3. 互动程度（评论、转发、点赞总量）
        
        Returns:
            {'level': '高/中/低', 'score': 0-100, 'factors': [...]}
        """
        if not data:
            return {'level': '低', 'score': 0, 'factors': []}
        
        total = len(data)
        factors = []
        risk_score = 0
        
        # 1. 负面情感占比 (最高40分)
        negative_count = sum(1 for d in data if d.get('sentiment_label') == 'negative')
        negative_ratio = negative_count / total
        sentiment_score = min(negative_ratio * 100, 40)
        risk_score += sentiment_score
        
        if negative_ratio > 0.3:
            factors.append(f"负面情感占比较高 ({negative_ratio:.1%})")
        
        # 2. 互动程度 (最高30分)
        total_interaction = sum(
            (d.get('like_count', 0) or 0) + 
            (d.get('comment_count', 0) or 0) + 
            (d.get('share_count', 0) or 0)
            for d in data
        )
        avg_interaction = total_interaction / total
        
        if avg_interaction > 1000:
            interaction_score = 30
            factors.append(f"平均互动量极高 ({avg_interaction:.0f})")
        elif avg_interaction > 500:
            interaction_score = 20
            factors.append(f"平均互动量较高 ({avg_interaction:.0f})")
        elif avg_interaction > 100:
            interaction_score = 10
        else:
            interaction_score = 0
        
        risk_score += interaction_score
        
        # 3. 传播速度 (最高30分)
        now = datetime.now()
        recent_count = 0
        for d in data:
            publish_time = d.get('publish_time')
            if isinstance(publish_time, datetime):
                if (now - publish_time).total_seconds() < 3600 * 24:  # 24小时内
                    recent_count += 1
        
        recent_ratio = recent_count / total if total > 0 else 0
        speed_score = min(recent_ratio * 60, 30)
        risk_score += speed_score
        
        if recent_ratio > 0.5:
            factors.append(f"近24小时内发布占比高 ({recent_ratio:.1%})")
        
        # 确定风险等级
        if risk_score >= 60:
            level = '高'
        elif risk_score >= 30:
            level = '中'
        else:
            level = '低'
        
        return {
            'level': level,
            'score': round(risk_score, 2),
            'factors': factors,
            'details': {
                'sentiment_score': round(sentiment_score, 2),
                'interaction_score': round(interaction_score, 2),
                'speed_score': round(speed_score, 2),
                'negative_ratio': round(negative_ratio, 4),
                'avg_interaction': round(avg_interaction, 2),
                'recent_ratio': round(recent_ratio, 4),
            }
        }
    
    def extract_keywords_from_data(
        self,
        data: List[Dict],
        top_n: int = 10
    ) -> List[Tuple[str, int]]:
        """
        从数据中提取关键词
        """
        from app.services.nlp_analyzer import get_nlp_analyzer
        
        texts = [d.get('content', '') for d in data if d.get('content')]
        
        analyzer = get_nlp_analyzer()
        return analyzer.extract_keywords_from_texts(texts, top_n)
    
    def get_sentiment_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """
        获取情感分析摘要
        """
        if not data:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_ratio': 0,
                'negative_ratio': 0,
                'neutral_ratio': 0,
            }
        
        total = len(data)
        positive = sum(1 for d in data if d.get('sentiment_label') == 'positive')
        negative = sum(1 for d in data if d.get('sentiment_label') == 'negative')
        neutral = total - positive - negative
        
        return {
            'total': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'positive_ratio': round(positive / total, 4) if total > 0 else 0,
            'negative_ratio': round(negative / total, 4) if total > 0 else 0,
            'neutral_ratio': round(neutral / total, 4) if total > 0 else 0,
        }


# 单例
_data_processor = None


def get_data_processor() -> DataProcessor:
    global _data_processor
    if _data_processor is None:
        _data_processor = DataProcessor()
    return _data_processor
