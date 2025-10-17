"""Analytics schemas"""
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class SentimentDistribution(BaseModel):
    """Sentiment distribution"""
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    total: int = 0


class TimeSeriesPoint(BaseModel):
    """Time series data point"""
    date: str
    count: int
    avg_sentiment: float = 0.5


class KeywordData(BaseModel):
    """Keyword frequency data"""
    word: str
    count: int


class AnalyticsSummary(BaseModel):
    """Analytics summary for a dataset"""
    dataset_id: Optional[int] = None
    total_records: int
    sentiment_distribution: SentimentDistribution
    avg_sentiment_score: float = 0.5
    time_series: List[TimeSeriesPoint] = []
    top_keywords: List[KeywordData] = []
    
    # Legacy fields for backward compatibility
    sentiment: Optional[SentimentDistribution] = None
    total_likes: int = 0
    total_shares: int = 0
    total_comments: int = 0
    avg_sentiment: Optional[float] = None
    trends: List[TimeSeriesPoint] = []
