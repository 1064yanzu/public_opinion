"""Analytics schemas"""
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime


class SentimentDistribution(BaseModel):
    """Sentiment distribution"""
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    total: int = 0


class ActivityTrend(BaseModel):
    """Activity trend data point"""
    date: str
    count: int
    likes: int
    shares: int
    comments: int


class AnalyticsSummary(BaseModel):
    """Analytics summary for a dataset"""
    dataset_id: int
    total_records: int
    sentiment: SentimentDistribution
    total_likes: int
    total_shares: int
    total_comments: int
    avg_sentiment: float
    trends: List[ActivityTrend]
    top_keywords: List[Dict[str, int]]
