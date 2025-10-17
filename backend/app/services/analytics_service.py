"""Analytics service for datasets"""
from collections import Counter
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.record import DataRecord
from ..schemas.analytics import AnalyticsSummary, SentimentDistribution, TimeSeriesPoint, KeywordData


class AnalyticsService:
    """Service for computing analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def dataset_summary(self, dataset_id: int, user_id: int) -> AnalyticsSummary:
        """Generate analytics summary for a dataset"""
        # Query dataset records for the user
        records = (
            self.db.query(DataRecord)
            .join(DataRecord.dataset)
            .filter(DataRecord.dataset_id == dataset_id)
            .filter(DataRecord.dataset.has(user_id=user_id))
            .all()
        )
        
        if not records:
            empty_sentiment = SentimentDistribution()
            return AnalyticsSummary(
                dataset_id=dataset_id,
                total_records=0,
                sentiment_distribution=empty_sentiment,
                sentiment=empty_sentiment,
                total_likes=0,
                total_shares=0,
                total_comments=0,
                avg_sentiment_score=0.0,
                avg_sentiment=0.0,
                time_series=[],
                trends=[],
                top_keywords=[],
            )
        
        # Sentiment distribution
        sentiment_counter = Counter(record.sentiment_label or "neutral" for record in records)
        positive = sentiment_counter.get("positive", 0)
        negative = sentiment_counter.get("negative", 0)
        neutral = sentiment_counter.get("neutral", 0)
        total = positive + negative + neutral
        
        sentiment = SentimentDistribution(
            positive=positive,
            negative=negative,
            neutral=neutral,
            total=total,
        )
        
        # Metrics
        total_likes = sum(record.likes or 0 for record in records)
        total_shares = sum(record.shares or 0 for record in records)
        total_comments = sum(record.comments or 0 for record in records)
        
        sentiment_scores = [record.sentiment_score for record in records if record.sentiment_score is not None]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        # Time series by day
        time_series_rows = (
            self.db.query(
                func.strftime("%Y-%m-%d", DataRecord.created_at).label("date"),
                func.count(DataRecord.id),
                func.avg(DataRecord.sentiment_score),
            )
            .filter(DataRecord.dataset_id == dataset_id)
            .group_by("date")
            .order_by("date")
            .all()
        )
        time_series = [
            TimeSeriesPoint(
                date=row[0],
                count=row[1] or 0,
                avg_sentiment=row[2] or 0.5,
            )
            for row in time_series_rows
        ]
        
        # Top keywords from content (simple splitting)
        word_counter = Counter()
        for record in records:
            if record.content:
                words = [
                    word.lower()
                    for word in record.content.split()
                    if len(word) > 1 and word.isalpha()
                ]
                word_counter.update(words)
        top_keywords = [
            KeywordData(word=keyword, count=count)
            for keyword, count in word_counter.most_common(10)
        ]
        
        return AnalyticsSummary(
            dataset_id=dataset_id,
            total_records=len(records),
            sentiment_distribution=sentiment,
            sentiment=sentiment,
            total_likes=total_likes,
            total_shares=total_shares,
            total_comments=total_comments,
            avg_sentiment_score=avg_sentiment,
            avg_sentiment=avg_sentiment,
            time_series=time_series,
            trends=time_series,
            top_keywords=top_keywords,
        )
