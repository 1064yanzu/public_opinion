"""
高级数据分析服务
包含 LDA 主题模型、关键传播主体识别、趋势分析等功能
这些功能对性能要求不高，适合实时分析
"""
import re
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta


class AdvancedAnalyzer:
    """高级分析器"""
    
    STOPWORDS = {
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '他', '她', '它', '们', '吧', '啊', '呢', '吗', '把', '被',
    }
    
    def __init__(self):
        self._jieba_loaded = False
    
    def _load_jieba(self):
        if not self._jieba_loaded:
            try:
                import jieba
                jieba.setLogLevel(20)
                self._jieba = jieba
                self._jieba_loaded = True
            except ImportError:
                self._jieba = None
    
    # ========== 关键传播主体识别 ==========
    
    def identify_key_spreaders(
        self,
        data: List[Dict[str, Any]],
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        识别关键传播主体
        
        基于多维度评估用户的传播影响力：
        1. 互动量（点赞、评论、转发）
        2. 发布频率
        3. 内容质量（平均互动量）
        4. 粉丝量（如有）
        
        Args:
            data: 包含用户信息的数据列表
            top_n: 返回前 N 个关键用户
            
        Returns:
            关键传播主体列表
        """
        user_stats = defaultdict(lambda: {
            'post_count': 0,
            'total_likes': 0,
            'total_comments': 0,
            'total_shares': 0,
            'followers': 0,
            'user_id': '',
        })
        
        for item in data:
            user_name = item.get('user_name') or item.get('author') or '未知用户'
            
            stats = user_stats[user_name]
            stats['post_count'] += 1
            stats['total_likes'] += item.get('like_count', 0) or 0
            stats['total_comments'] += item.get('comment_count', 0) or 0
            stats['total_shares'] += item.get('share_count', 0) or 0
            stats['user_id'] = item.get('user_id') or item.get('author_id') or ''
            
            # 更新粉丝数（取最大值）
            followers = item.get('followers_count', 0) or 0
            if followers > stats['followers']:
                stats['followers'] = followers
        
        # 计算影响力分数
        result = []
        for user_name, stats in user_stats.items():
            # 总互动量
            total_interaction = (
                stats['total_likes'] + 
                stats['total_comments'] * 2 +  # 评论权重更高
                stats['total_shares'] * 3  # 转发权重最高
            )
            
            # 平均互动量
            avg_interaction = total_interaction / max(stats['post_count'], 1)
            
            # 综合影响力分数
            # 考虑发布频率、互动量、粉丝数
            influence_score = (
                total_interaction * 0.4 +
                avg_interaction * stats['post_count'] * 0.3 +
                (stats['followers'] / 1000) * 0.3  # 粉丝数归一化
            )
            
            result.append({
                'user_name': user_name,
                'user_id': stats['user_id'],
                'post_count': stats['post_count'],
                'total_likes': stats['total_likes'],
                'total_comments': stats['total_comments'],
                'total_shares': stats['total_shares'],
                'followers': stats['followers'],
                'avg_interaction': round(avg_interaction, 2),
                'influence_score': round(influence_score, 2),
            })
        
        # 按影响力排序
        result.sort(key=lambda x: x['influence_score'], reverse=True)
        return result[:top_n]
    
    # ========== 简化版 LDA 主题模型 ==========
    
    def simple_topic_clustering(
        self,
        texts: List[str],
        n_topics: int = 5,
        words_per_topic: int = 10
    ) -> List[Dict[str, Any]]:
        """
        简化版主题聚类
        
        使用基于词频的简单方法进行主题聚类，
        不需要复杂的 LDA 库，性能开销小
        
        Args:
            texts: 文本列表
            n_topics: 主题数量
            words_per_topic: 每个主题的关键词数
            
        Returns:
            主题列表
        """
        self._load_jieba()
        
        if not self._jieba or not texts:
            return []
        
        # 文档词频矩阵
        doc_words = []
        all_words = Counter()
        
        for text in texts:
            text = self._clean_text(text)
            if not text:
                continue
            
            words = [
                w for w in self._jieba.cut(text)
                if len(w) >= 2 and w not in self.STOPWORDS
                and re.search(r'[\u4e00-\u9fff]', w)
            ]
            
            doc_words.append(Counter(words))
            all_words.update(words)
        
        if not doc_words:
            return []
        
        # 获取高频词作为主题种子
        top_words = [w for w, _ in all_words.most_common(n_topics * words_per_topic)]
        
        # 简单聚类：将文档分配到最相关的主题
        topics = [Counter() for _ in range(n_topics)]
        topic_docs = [[] for _ in range(n_topics)]
        
        for i, doc in enumerate(doc_words):
            if not doc:
                continue
            
            # 计算文档与每个主题种子词的相关性
            scores = []
            for t in range(n_topics):
                seed_start = t * words_per_topic
                seed_end = seed_start + words_per_topic
                seed_words = set(top_words[seed_start:seed_end])
                
                score = sum(doc.get(w, 0) for w in seed_words)
                scores.append(score)
            
            # 分配到得分最高的主题
            if max(scores) > 0:
                best_topic = scores.index(max(scores))
                topics[best_topic].update(doc)
                topic_docs[best_topic].append(i)
        
        # 构建结果
        result = []
        for t in range(n_topics):
            top_words_in_topic = topics[t].most_common(words_per_topic)
            if top_words_in_topic:
                result.append({
                    'topic_id': t + 1,
                    'keywords': [w for w, _ in top_words_in_topic],
                    'keyword_weights': [
                        {'word': w, 'weight': round(c / max(sum(topics[t].values()), 1), 4)}
                        for w, c in top_words_in_topic
                    ],
                    'doc_count': len(topic_docs[t]),
                    'doc_ratio': round(len(topic_docs[t]) / max(len(doc_words), 1), 4),
                })
        
        # 按文档数排序
        result.sort(key=lambda x: x['doc_count'], reverse=True)
        return result
    
    # ========== 趋势分析 ==========
    
    def analyze_trend(
        self,
        data: List[Dict[str, Any]],
        time_field: str = 'publish_time',
        interval: str = 'day'  # 'hour', 'day', 'week'
    ) -> Dict[str, Any]:
        """
        趋势分析
        
        Args:
            data: 数据列表
            time_field: 时间字段名
            interval: 时间间隔
            
        Returns:
            趋势分析结果
        """
        if not data:
            return {'timeline': [], 'stats': {}}
        
        # 按时间分组
        time_groups = defaultdict(list)
        
        for item in data:
            time_value = item.get(time_field)
            if not time_value:
                continue
            
            # 转换时间
            if isinstance(time_value, str):
                try:
                    time_value = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                except:
                    continue
            elif not isinstance(time_value, datetime):
                continue
            
            # 生成时间键
            if interval == 'hour':
                key = time_value.strftime('%Y-%m-%d %H:00')
            elif interval == 'week':
                # 获取周一
                monday = time_value - timedelta(days=time_value.weekday())
                key = monday.strftime('%Y-%m-%d')
            else:  # day
                key = time_value.strftime('%Y-%m-%d')
            
            time_groups[key].append(item)
        
        # 生成时间线数据
        timeline = []
        for time_key in sorted(time_groups.keys()):
            items = time_groups[time_key]
            
            # 统计
            total_likes = sum(i.get('like_count', 0) or 0 for i in items)
            total_comments = sum(i.get('comment_count', 0) or 0 for i in items)
            total_shares = sum(i.get('share_count', 0) or 0 for i in items)
            
            # 情感统计
            positive = sum(1 for i in items if i.get('sentiment_label') == 'positive')
            negative = sum(1 for i in items if i.get('sentiment_label') == 'negative')
            
            timeline.append({
                'time': time_key,
                'count': len(items),
                'likes': total_likes,
                'comments': total_comments,
                'shares': total_shares,
                'positive': positive,
                'negative': negative,
                'sentiment_ratio': round(positive / max(len(items), 1), 4),
            })
        
        # 总体统计
        total_count = len(data)
        stats = {
            'total': total_count,
            'time_range': {
                'start': min(time_groups.keys()) if time_groups else None,
                'end': max(time_groups.keys()) if time_groups else None,
            },
            'peak_time': max(timeline, key=lambda x: x['count'])['time'] if timeline else None,
            'avg_per_period': round(total_count / max(len(timeline), 1), 2),
        }
        
        return {'timeline': timeline, 'stats': stats}
    
    # ========== 地域分析 ==========
    
    def analyze_geography(
        self,
        data: List[Dict[str, Any]],
        province_field: str = 'province'
    ) -> Dict[str, Any]:
        """
        地域分析
        
        Args:
            data: 数据列表
            province_field: 省份字段名
            
        Returns:
            地域分析结果
        """
        province_stats = defaultdict(lambda: {
            'count': 0,
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'positive': 0,
            'negative': 0,
        })
        
        for item in data:
            province = item.get(province_field, '') or '未知'
            if province in ['N/A', '', 'nan', 'None']:
                province = '未知'
            
            stats = province_stats[province]
            stats['count'] += 1
            stats['likes'] += item.get('like_count', 0) or 0
            stats['comments'] += item.get('comment_count', 0) or 0
            stats['shares'] += item.get('share_count', 0) or 0
            
            if item.get('sentiment_label') == 'positive':
                stats['positive'] += 1
            elif item.get('sentiment_label') == 'negative':
                stats['negative'] += 1
        
        # 转换为列表
        result = []
        for province, stats in province_stats.items():
            if province == '未知':
                continue
            result.append({
                'province': province,
                **stats,
                'avg_interaction': round(
                    (stats['likes'] + stats['comments'] + stats['shares']) / max(stats['count'], 1), 2
                ),
            })
        
        # 排序
        result.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'provinces': result,
            'total_provinces': len(result),
            'top_province': result[0]['province'] if result else None,
        }
    
    # ========== 情感演化分析 ==========
    
    def analyze_sentiment_evolution(
        self,
        data: List[Dict[str, Any]],
        time_field: str = 'publish_time'
    ) -> Dict[str, Any]:
        """
        情感演化分析
        
        分析情感随时间的变化趋势
        """
        trend = self.analyze_trend(data, time_field, interval='day')
        
        evolution = []
        for point in trend['timeline']:
            total = point['count']
            if total == 0:
                continue
            
            evolution.append({
                'time': point['time'],
                'positive_ratio': round(point['positive'] / total, 4),
                'negative_ratio': round(point['negative'] / total, 4),
                'neutral_ratio': round(1 - point['positive'] / total - point['negative'] / total, 4),
                'total': total,
            })
        
        # 计算情感变化趋势
        if len(evolution) >= 2:
            first_positive = evolution[0]['positive_ratio']
            last_positive = evolution[-1]['positive_ratio']
            trend_direction = 'improving' if last_positive > first_positive else (
                'declining' if last_positive < first_positive else 'stable'
            )
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'evolution': evolution,
            'trend_direction': trend_direction,
        }
    
    # ========== 热词对比 ==========
    
    def compare_keywords(
        self,
        positive_texts: List[str],
        negative_texts: List[str],
        top_n: int = 15
    ) -> Dict[str, List[Tuple[str, int]]]:
        """
        对比正负面文本的关键词
        
        Returns:
            {'positive': [...], 'negative': [...], 'common': [...]}
        """
        self._load_jieba()
        
        if not self._jieba:
            return {'positive': [], 'negative': [], 'common': []}
        
        def get_words(texts):
            freq = Counter()
            for text in texts:
                text = self._clean_text(text)
                if not text:
                    continue
                words = [
                    w for w in self._jieba.cut(text)
                    if len(w) >= 2 and w not in self.STOPWORDS
                    and re.search(r'[\u4e00-\u9fff]', w)
                ]
                freq.update(words)
            return freq
        
        pos_freq = get_words(positive_texts)
        neg_freq = get_words(negative_texts)
        
        # 找出差异词和共同词
        pos_unique = []
        neg_unique = []
        common = []
        
        all_words = set(pos_freq.keys()) | set(neg_freq.keys())
        
        for word in all_words:
            pos_count = pos_freq.get(word, 0)
            neg_count = neg_freq.get(word, 0)
            
            if pos_count > 0 and neg_count > 0:
                common.append((word, pos_count + neg_count))
            elif pos_count > neg_count * 2:  # 正面专属词
                pos_unique.append((word, pos_count))
            elif neg_count > pos_count * 2:  # 负面专属词
                neg_unique.append((word, neg_count))
        
        return {
            'positive': sorted(pos_unique, key=lambda x: x[1], reverse=True)[:top_n],
            'negative': sorted(neg_unique, key=lambda x: x[1], reverse=True)[:top_n],
            'common': sorted(common, key=lambda x: x[1], reverse=True)[:top_n],
        }
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        text = re.sub(r'http[s]?://[^\s]+', '', str(text))
        text = re.sub(r'@[\w\-]+', '', text)
        text = re.sub(r'#[^#]+#', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()


# 单例
_advanced_analyzer = None


def get_advanced_analyzer() -> AdvancedAnalyzer:
    global _advanced_analyzer
    if _advanced_analyzer is None:
        _advanced_analyzer = AdvancedAnalyzer()
    return _advanced_analyzer
