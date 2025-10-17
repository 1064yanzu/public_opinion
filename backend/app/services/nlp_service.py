"""NLP service for sentiment analysis"""
from typing import Tuple
from snownlp import SnowNLP


class NLPService:
    """Service for natural language processing"""
    
    @staticmethod
    def analyze_sentiment(text: str) -> Tuple[float, str]:
        """
        Analyze sentiment of text
        Returns: (sentiment_score, sentiment_label)
        sentiment_score: float between 0 and 1
        sentiment_label: 'positive', 'negative', or 'neutral'
        """
        if not text or not isinstance(text, str):
            return 0.5, "neutral"
        
        try:
            score = SnowNLP(text).sentiments
            
            # Categorize
            if score > 0.6:
                label = "positive"
            elif score < 0.4:
                label = "negative"
            else:
                label = "neutral"
            
            return score, label
        except Exception:
            return 0.5, "neutral"
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 10):
        """Extract keywords from text"""
        if not text or not isinstance(text, str):
            return []
        
        try:
            s = SnowNLP(text)
            return s.keywords(top_n)
        except Exception:
            return []
