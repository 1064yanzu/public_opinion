"""
NLP 分析服务
包含情感分析、关键词提取、文本分类等功能
"""
import re
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter


class NLPAnalyzer:
    """NLP 分析器"""
    
    # 中文停用词（精简版）
    STOPWORDS = {
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '他', '她', '它', '们', '吧', '啊', '呢', '吗', '把', '被',
        '让', '给', '可以', '可能', '还', '而', '但', '只', '所以', '因为', '如果', '这个',
        '那个', '什么', '怎么', '为什么', '哪', '谁', '这样', '那样', '这些', '那些',
        '呵呵', '哈哈', '嘻嘻', '转发', '微博', '视频', '图片', '链接', '网页',
    }
    
    def __init__(self):
        self._jieba_loaded = False
        self._snownlp_loaded = False
    
    def _load_jieba(self):
        """延迟加载 jieba"""
        if not self._jieba_loaded:
            try:
                import jieba
                jieba.setLogLevel(20)  # 关闭调试信息
                self._jieba = jieba
                self._jieba_loaded = True
            except ImportError:
                self._jieba = None
                print("警告: jieba 未安装，关键词提取功能不可用")
    
    def _load_snownlp(self):
        """延迟加载 snownlp"""
        if not self._snownlp_loaded:
            try:
                from snownlp import SnowNLP
                self._snownlp = SnowNLP
                self._snownlp_loaded = True
            except ImportError:
                self._snownlp = None
                print("警告: snownlp 未安装，情感分析功能不可用")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        text = str(text)
        
        # 移除 URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 移除 @用户
        text = re.sub(r'@[\w\-]+', '', text)
        
        # 移除话题标签
        text = re.sub(r'#[^#]+#', '', text)
        
        # 移除表情符号
        text = re.sub(r'\[.*?\]', '', text)
        
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        情感分析
        
        Returns:
            {'score': 0.0-1.0, 'label': 'positive/negative/neutral'}
        """
        self._load_snownlp()
        
        if not text or not self._snownlp:
            return {'score': 0.5, 'label': 'neutral'}
        
        try:
            cleaned_text = self.clean_text(text)
            if not cleaned_text:
                return {'score': 0.5, 'label': 'neutral'}
            
            s = self._snownlp(cleaned_text)
            score = s.sentiments
            
            # 分类
            if score > 0.6:
                label = 'positive'
            elif score < 0.4:
                label = 'negative'
            else:
                label = 'neutral'
            
            return {'score': round(score, 4), 'label': label}
            
        except Exception as e:
            print(f"情感分析出错: {e}")
            return {'score': 0.5, 'label': 'neutral'}
    
    def batch_sentiment_analysis(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量情感分析"""
        return [self.sentiment_analysis(text) for text in texts]
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        提取关键词
        
        Returns:
            [(keyword, weight), ...]
        """
        self._load_jieba()
        
        if not text or not self._jieba:
            return []
        
        try:
            import jieba.analyse
            
            cleaned_text = self.clean_text(text)
            if not cleaned_text:
                return []
            
            # 使用 TF-IDF 提取关键词
            keywords = jieba.analyse.extract_tags(
                cleaned_text, 
                topK=top_n, 
                withWeight=True
            )
            
            # 过滤停用词
            filtered = [
                (word, weight) for word, weight in keywords 
                if word not in self.STOPWORDS and len(word) >= 2
            ]
            
            return filtered[:top_n]
            
        except Exception as e:
            print(f"关键词提取出错: {e}")
            return []
    
    def extract_keywords_from_texts(self, texts: List[str], top_n: int = 20) -> List[Tuple[str, int]]:
        """
        从多个文本中提取关键词
        
        Returns:
            [(keyword, count), ...]
        """
        self._load_jieba()
        
        if not texts or not self._jieba:
            return []
        
        try:
            word_freq = Counter()
            
            for text in texts:
                cleaned = self.clean_text(text)
                if not cleaned:
                    continue
                
                words = self._jieba.cut(cleaned)
                for word in words:
                    word = word.strip()
                    # 过滤条件
                    if (word and 
                        len(word) >= 2 and 
                        word not in self.STOPWORDS and
                        re.search(r'[\u4e00-\u9fff]', word)):  # 包含中文
                        word_freq[word] += 1
            
            return word_freq.most_common(top_n)
            
        except Exception as e:
            print(f"批量关键词提取出错: {e}")
            return []
    
    def word_frequency(self, texts: List[str], min_length: int = 2) -> Dict[str, int]:
        """
        词频统计
        
        Returns:
            {word: count, ...}
        """
        self._load_jieba()
        
        if not texts or not self._jieba:
            return {}
        
        try:
            freq = Counter()
            
            for text in texts:
                cleaned = self.clean_text(text)
                if not cleaned:
                    continue
                
                words = self._jieba.cut(cleaned)
                for word in words:
                    word = word.strip()
                    if (word and 
                        len(word) >= min_length and 
                        word not in self.STOPWORDS):
                        freq[word] += 1
            
            return dict(freq)
            
        except Exception as e:
            print(f"词频统计出错: {e}")
            return {}
    
    def summarize(self, text: str, sentences: int = 3) -> List[str]:
        """
        文本摘要
        
        Returns:
            摘要句子列表
        """
        self._load_snownlp()
        
        if not text or not self._snownlp:
            return []
        
        try:
            cleaned = self.clean_text(text)
            if not cleaned or len(cleaned) < 50:
                return [cleaned] if cleaned else []
            
            s = self._snownlp(cleaned)
            summary = s.summary(sentences)
            return summary if isinstance(summary, list) else [summary]
            
        except Exception as e:
            print(f"文本摘要出错: {e}")
            return []


# 单例实例
_nlp_analyzer = None


def get_nlp_analyzer() -> NLPAnalyzer:
    """获取 NLP 分析器单例"""
    global _nlp_analyzer
    if _nlp_analyzer is None:
        _nlp_analyzer = NLPAnalyzer()
    return _nlp_analyzer
