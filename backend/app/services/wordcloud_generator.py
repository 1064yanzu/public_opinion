"""
词云生成服务
独立实现，不依赖原项目代码
"""
import os
import re
import sys
from typing import List, Dict, Optional, Tuple
from collections import Counter
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.core.paths import PROJECT_ROOT


class WordCloudGenerator:
    """词云生成器"""
    
    # 中文停用词
    STOPWORDS = {
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '他', '她', '它', '们', '吧', '啊', '呢', '吗', '把', '被',
        '让', '给', '可以', '可能', '还', '而', '但', '只', '所以', '因为', '如果', '这个',
        '那个', '什么', '怎么', '为什么', '哪', '谁', '这样', '那样', '这些', '那些',
        '呵呵', '哈哈', '嘻嘻', '转发', '微博', '视频', '图片', '链接', '网页',
        '真的', '觉得', '知道', '应该', '现在', '时候', '然后', '已经', '还是',
    }
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or settings.WORDCLOUD_DIR
        self._jieba_loaded = False
        self._wordcloud_loaded = False
    
    def _load_jieba(self):
        """延迟加载 jieba"""
        if not self._jieba_loaded:
            try:
                import jieba
                jieba.setLogLevel(20)
                self._jieba = jieba
                self._jieba_loaded = True
            except ImportError:
                self._jieba = None
                print("警告: jieba 未安装")
    
    def _load_wordcloud(self):
        """延迟加载 wordcloud"""
        if not self._wordcloud_loaded:
            try:
                import wordcloud as wc
                self._wordcloud = wc
                self._wordcloud_loaded = True
            except ImportError:
                self._wordcloud = None
                print("警告: wordcloud 未安装")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        text = str(text)
        
        # 移除 URL
        text = re.sub(r'http[s]?://[^\s]+', '', text)
        # 移除 @用户
        text = re.sub(r'@[\w\-]+', '', text)
        # 移除话题
        text = re.sub(r'#[^#]+#', '', text)
        # 移除表情
        text = re.sub(r'\[.*?\]', '', text)
        # 移除 HTML
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符
        text = re.sub(r'[^\u4e00-\u9fffa-zA-Z0-9\s]', '', text)
        
        return text.strip()
    
    def segment_text(self, text: str) -> List[str]:
        """分词"""
        self._load_jieba()
        
        if not self._jieba:
            return []
        
        cleaned = self.clean_text(text)
        if not cleaned:
            return []
        
        words = self._jieba.cut(cleaned)
        result = []
        
        for word in words:
            word = word.strip()
            if (word and 
                len(word) >= 2 and 
                word not in self.STOPWORDS and
                not word.isdigit() and
                re.search(r'[\u4e00-\u9fff]', word)):
                result.append(word)
        
        return result
    
    def calculate_word_freq(self, texts: List[str], top_n: int = 200) -> Dict[str, int]:
        """
        计算词频
        
        Args:
            texts: 文本列表
            top_n: 返回前 N 个高频词
            
        Returns:
            {word: count, ...}
        """
        freq = Counter()
        
        for text in texts:
            words = self.segment_text(text)
            freq.update(words)
        
        # 返回前 N 个
        return dict(freq.most_common(top_n))
    
    def generate(
        self,
        texts: List[str],
        filename: Optional[str] = None,
        width: int = 800,
        height: int = 600,
        max_words: int = 200,
        background_color: str = 'white',
        colormap: str = 'viridis'
    ) -> Tuple[Optional[str], Dict[str, int]]:
        """
        生成词云
        
        Args:
            texts: 文本列表
            filename: 输出文件名（不含路径）
            width: 宽度
            height: 高度
            max_words: 最大词数
            background_color: 背景色
            colormap: 颜色映射
            
        Returns:
            (image_path, word_freq) 或 (None, word_freq)
        """
        self._load_jieba()
        self._load_wordcloud()
        
        # 计算词频
        word_freq = self.calculate_word_freq(texts, max_words)
        
        if not word_freq:
            return None, {}
        
        if not self._wordcloud:
            # 无法生成图片，只返回词频
            return None, word_freq
        
        try:
            # 查找中文字体
            font_path = self._find_chinese_font()
            
            # 创建词云
            wc = self._wordcloud.WordCloud(
                width=width,
                height=height,
                max_words=max_words,
                background_color=background_color,
                font_path=font_path,
                colormap=colormap,
                collocations=False,
                min_font_size=10,
                max_font_size=150,
                random_state=42,
            )
            
            wc.generate_from_frequencies(word_freq)
            
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"wordcloud_{timestamp}.png"
            
            output_path = os.path.join(self.output_dir, filename)
            wc.to_file(output_path)
            
            print(f"词云已保存: {output_path}")
            return output_path, word_freq
            
        except Exception as e:
            print(f"生成词云出错: {e}")
            return None, word_freq
    
    def _find_chinese_font(self) -> Optional[str]:
        """查找中文字体"""
        import platform
        
        system = platform.system()
        
        # 常见中文字体路径
        font_paths = []
        
        if system == 'Darwin':  # macOS
            font_paths = [
                str(Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / 'sanjipomoti.ttf'),
                str(Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / '三极泼墨体.ttf'),
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Medium.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
            ]
        elif system == 'Windows':
            font_paths = [
                str(Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / 'sanjipomoti.ttf'),
                str(Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / '三极泼墨体.ttf'),
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/simsun.ttc',
            ]
        else:  # Linux
            font_paths = [
                str(Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / 'sanjipomoti.ttf'),
                str(Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / '三极泼墨体.ttf'),
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        
        return None


# 便捷函数
def generate_wordcloud(
    texts: List[str],
    output_dir: Optional[str] = None,
    **kwargs
) -> Tuple[Optional[str], Dict[str, int]]:
    """生成词云的便捷函数"""
    generator = WordCloudGenerator(output_dir)
    return generator.generate(texts, **kwargs)
