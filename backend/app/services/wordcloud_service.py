"""Wordcloud generation service"""
import jieba
from wordcloud import WordCloud
import numpy as np
from PIL import Image
import io
import base64
from typing import Optional, List, Dict
from pathlib import Path
import re


class WordCloudService:
    """Service for generating word clouds"""
    
    def __init__(self, stopwords_path: Optional[str] = None):
        # Load stopwords
        self.stopwords = set()
        if stopwords_path and Path(stopwords_path).exists():
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                self.stopwords = set(line.strip() for line in f)
        
        # Default font path
        self.font_path = self._find_font()
    
    def _find_font(self) -> Optional[str]:
        """Find available Chinese font"""
        possible_fonts = [
            './三极泼墨体.ttf',
            './fonts/三极泼墨体.ttf',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
        ]
        
        for font_path in possible_fonts:
            if Path(font_path).exists():
                return font_path
        
        return None
    
    def clean_text(self, text: str) -> str:
        """Clean text by removing URLs, mentions, hashtags, etc."""
        if not text:
            return ""
        
        text = str(text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove @mentions
        text = re.sub(r'@[\w\-]+', '', text)
        
        # Remove hashtags
        text = re.sub(r'#.*?#', '', text)
        
        # Remove emoji brackets
        text = re.sub(r'\[.*?\]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def segment_text(self, text: str) -> List[str]:
        """Segment text and remove stopwords"""
        if not text:
            return []
        
        # Clean text
        text = self.clean_text(text)
        
        # Segment
        words = jieba.cut(text)
        
        # Filter stopwords and short words
        filtered_words = [
            word for word in words
            if len(word) > 1 and word not in self.stopwords and word.strip()
        ]
        
        return filtered_words
    
    def generate_wordcloud(
        self,
        texts: List[str],
        mask_image_path: Optional[str] = None,
        width: int = 800,
        height: int = 600,
        background_color: str = 'white',
        max_words: int = 200,
        colormap: str = 'viridis'
    ) -> Dict[str, any]:
        """
        Generate word cloud from texts
        
        Args:
            texts: List of text strings
            mask_image_path: Path to mask image (optional)
            width: Width of output image
            height: Height of output image
            background_color: Background color
            max_words: Maximum number of words
            colormap: Matplotlib colormap name
            
        Returns:
            Dict with 'image_base64' and 'word_frequencies'
        """
        # Combine and segment all texts
        all_words = []
        for text in texts:
            all_words.extend(self.segment_text(text))
        
        if not all_words:
            raise ValueError("No valid words found in texts")
        
        # Create word frequency string
        word_text = ' '.join(all_words)
        
        # Prepare mask if provided
        mask = None
        if mask_image_path and Path(mask_image_path).exists():
            try:
                mask_img = Image.open(mask_image_path)
                mask = np.array(mask_img)
            except Exception as e:
                print(f"Failed to load mask image: {e}")
        
        # Generate wordcloud
        wc_params = {
            'font_path': self.font_path,
            'width': width,
            'height': height,
            'background_color': background_color,
            'max_words': max_words,
            'colormap': colormap,
            'relative_scaling': 0.5,
            'min_font_size': 10,
        }
        
        if mask is not None:
            wc_params['mask'] = mask
        
        wc = WordCloud(**wc_params)
        wc.generate(word_text)
        
        # Convert to image
        image = wc.to_image()
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Get word frequencies
        word_frequencies = wc.words_
        
        return {
            'image_base64': image_base64,
            'word_frequencies': word_frequencies,
            'total_words': len(all_words),
            'unique_words': len(set(all_words))
        }
    
    def generate_from_records(
        self,
        records: List[Dict],
        content_field: str = 'content',
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate wordcloud from data records
        
        Args:
            records: List of record dictionaries
            content_field: Field name containing text content
            **kwargs: Additional parameters for generate_wordcloud
            
        Returns:
            Wordcloud result dict
        """
        texts = [record.get(content_field, '') for record in records]
        texts = [text for text in texts if text]  # Filter empty
        
        if not texts:
            raise ValueError("No text content found in records")
        
        return self.generate_wordcloud(texts, **kwargs)
    
    def get_top_keywords(
        self,
        texts: List[str],
        top_n: int = 20
    ) -> List[Dict[str, any]]:
        """
        Extract top keywords from texts
        
        Args:
            texts: List of text strings
            top_n: Number of top keywords to return
            
        Returns:
            List of {'word': str, 'frequency': int} dicts
        """
        from collections import Counter
        
        all_words = []
        for text in texts:
            all_words.extend(self.segment_text(text))
        
        if not all_words:
            return []
        
        word_counts = Counter(all_words)
        top_words = word_counts.most_common(top_n)
        
        return [
            {'word': word, 'frequency': count}
            for word, count in top_words
        ]
