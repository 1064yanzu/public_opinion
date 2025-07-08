"""
轻量级主题聚类功能
提供多种聚类方案，资源占用低
"""
import os
import jieba
import jieba.posseg
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity
import re
from typing import List, Dict, Tuple, Any


class LightweightTopicClustering:
    """轻量级主题聚类器"""
    
    def __init__(self, method='keyword_based', num_topics=5, min_samples=3):
        """
        初始化聚类器
        
        Args:
            method: 聚类方法 ('keyword_based', 'kmeans', 'lda', 'dbscan')
            num_topics: 主题数量
            min_samples: 最小样本数
        """
        self.method = method
        self.num_topics = num_topics
        self.min_samples = min_samples
        self.stopwords = self._load_stopwords()
        
    def _load_stopwords(self) -> set:
        """加载停用词"""
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么', '可以', '这个', '中', '么', '出', '比', '还', '多', '对', '于', '学', '下', '地', '过', '他', '时', '来', '其', '里', '后', '自', '以', '会', '家', '可', '下', '而', '生', '大', '年', '同', '作', '并', '能'
        }
        
        # 尝试加载自定义停用词文件
        stopwords_file = os.getenv('STOPWORDS_FILE', 'data/stopwords.txt')
        if os.path.exists(stopwords_file):
            try:
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    custom_stopwords = set(line.strip() for line in f if line.strip())
                stopwords.update(custom_stopwords)
            except Exception as e:
                print(f"加载停用词文件失败: {e}")
        
        return stopwords
    
    def preprocess_text(self, text: str) -> List[str]:
        """文本预处理"""
        if not text or pd.isna(text):
            return []
        
        # 清理文本
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', str(text))
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 分词并过滤
        words = []
        for word, flag in jieba.posseg.cut(text):
            if (len(word) >= 2 and 
                word not in self.stopwords and 
                flag in ['n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'ad']):
                words.append(word)
        
        return words
    
    def keyword_based_clustering(self, texts: List[str]) -> Dict[str, Any]:
        """基于关键词的聚类（最轻量级）"""
        print("使用关键词聚类方法...")
        
        # 提取所有关键词
        all_keywords = []
        text_keywords = []
        
        for text in texts:
            keywords = self.preprocess_text(text)
            text_keywords.append(keywords)
            all_keywords.extend(keywords)
        
        # 统计关键词频率
        keyword_freq = Counter(all_keywords)
        top_keywords = [word for word, freq in keyword_freq.most_common(50) if freq >= 2]
        
        # 基于关键词相似度聚类
        clusters = defaultdict(list)
        cluster_keywords = {}
        
        for i, keywords in enumerate(text_keywords):
            if not keywords:
                clusters['其他'].append(i)
                continue
            
            # 找到最匹配的主题关键词
            best_topic = None
            best_score = 0
            
            for keyword in keywords:
                if keyword in top_keywords:
                    topic_name = keyword
                    score = keyword_freq[keyword]
                    
                    if score > best_score:
                        best_score = score
                        best_topic = topic_name
            
            if best_topic:
                clusters[best_topic].append(i)
                if best_topic not in cluster_keywords:
                    cluster_keywords[best_topic] = []
                cluster_keywords[best_topic].extend(keywords)
            else:
                clusters['其他'].append(i)
        
        # 生成主题摘要
        topics = []
        for topic_name, indices in clusters.items():
            if len(indices) >= self.min_samples:
                keywords = cluster_keywords.get(topic_name, [])
                keyword_counter = Counter(keywords)
                top_words = [word for word, _ in keyword_counter.most_common(5)]
                
                topics.append({
                    'topic_id': len(topics),
                    'topic_name': topic_name,
                    'keywords': top_words,
                    'document_count': len(indices),
                    'document_indices': indices,
                    'weight': len(indices) / len(texts)
                })
        
        return {
            'topics': topics,
            'method': 'keyword_based',
            'total_documents': len(texts),
            'clustered_documents': sum(len(topic['document_indices']) for topic in topics)
        }
    
    def kmeans_clustering(self, texts: List[str]) -> Dict[str, Any]:
        """K-means聚类"""
        print("使用K-means聚类方法...")
        
        # 文本预处理
        processed_texts = []
        for text in texts:
            words = self.preprocess_text(text)
            processed_texts.append(' '.join(words))
        
        # TF-IDF向量化
        vectorizer = TfidfVectorizer(
            max_features=1000,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 2)
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(processed_texts)
            
            # K-means聚类
            kmeans = KMeans(n_clusters=self.num_topics, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # 提取主题关键词
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            
            for i in range(self.num_topics):
                # 获取聚类中心的特征权重
                center = kmeans.cluster_centers_[i]
                top_indices = center.argsort()[-10:][::-1]
                keywords = [feature_names[idx] for idx in top_indices]
                
                # 获取属于该聚类的文档
                doc_indices = [idx for idx, label in enumerate(cluster_labels) if label == i]
                
                if len(doc_indices) >= self.min_samples:
                    topics.append({
                        'topic_id': i,
                        'topic_name': f"主题{i+1}",
                        'keywords': keywords[:5],
                        'document_count': len(doc_indices),
                        'document_indices': doc_indices,
                        'weight': len(doc_indices) / len(texts)
                    })
            
            return {
                'topics': topics,
                'method': 'kmeans',
                'total_documents': len(texts),
                'clustered_documents': sum(len(topic['document_indices']) for topic in topics)
            }
            
        except Exception as e:
            print(f"K-means聚类失败: {e}")
            return self.keyword_based_clustering(texts)
    
    def lda_clustering(self, texts: List[str]) -> Dict[str, Any]:
        """LDA主题模型"""
        print("使用LDA主题模型...")
        
        # 文本预处理
        processed_texts = []
        for text in texts:
            words = self.preprocess_text(text)
            processed_texts.append(' '.join(words))
        
        # TF-IDF向量化
        vectorizer = TfidfVectorizer(
            max_features=500,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 1)
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(processed_texts)
            
            # LDA模型
            lda = LatentDirichletAllocation(
                n_components=self.num_topics,
                random_state=42,
                max_iter=10,
                learning_method='batch'
            )
            
            doc_topic_matrix = lda.fit_transform(tfidf_matrix)
            
            # 提取主题关键词
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            
            for i in range(self.num_topics):
                # 获取主题的词分布
                topic_words = lda.components_[i]
                top_indices = topic_words.argsort()[-10:][::-1]
                keywords = [feature_names[idx] for idx in top_indices]
                
                # 获取属于该主题的文档（概率最高的主题）
                doc_indices = [idx for idx, topic_probs in enumerate(doc_topic_matrix) 
                             if topic_probs.argmax() == i and topic_probs.max() > 0.3]
                
                if len(doc_indices) >= self.min_samples:
                    topics.append({
                        'topic_id': i,
                        'topic_name': f"主题{i+1}",
                        'keywords': keywords[:5],
                        'document_count': len(doc_indices),
                        'document_indices': doc_indices,
                        'weight': len(doc_indices) / len(texts)
                    })
            
            return {
                'topics': topics,
                'method': 'lda',
                'total_documents': len(texts),
                'clustered_documents': sum(len(topic['document_indices']) for topic in topics)
            }
            
        except Exception as e:
            print(f"LDA聚类失败: {e}")
            return self.keyword_based_clustering(texts)
    
    def cluster_texts(self, texts: List[str]) -> Dict[str, Any]:
        """执行文本聚类"""
        if not texts:
            return {'topics': [], 'method': self.method, 'total_documents': 0, 'clustered_documents': 0}
        
        print(f"开始聚类 {len(texts)} 个文本，使用方法: {self.method}")
        
        if self.method == 'keyword_based':
            return self.keyword_based_clustering(texts)
        elif self.method == 'kmeans':
            return self.kmeans_clustering(texts)
        elif self.method == 'lda':
            return self.lda_clustering(texts)
        else:
            print(f"未知聚类方法: {self.method}，使用默认关键词方法")
            return self.keyword_based_clustering(texts)


def create_topic_clustering() -> LightweightTopicClustering:
    """根据环境变量创建主题聚类器"""
    method = os.getenv('CLUSTERING_METHOD', 'keyword_based').lower()
    num_topics = int(os.getenv('CLUSTERING_NUM_TOPICS', '5'))
    min_samples = int(os.getenv('CLUSTERING_MIN_SAMPLES', '3'))
    
    return LightweightTopicClustering(method, num_topics, min_samples)
