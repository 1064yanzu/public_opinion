"""Analytics service for datasets"""
from collections import Counter
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.record import DataRecord
from ..schemas.analytics import AnalyticsSummary, SentimentDistribution, ActivityTrend


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
            return AnalyticsSummary(
                dataset_id=dataset_id,
                total_records=0,
                sentiment=SentimentDistribution(),
                total_likes=0,
                total_shares=0,
                total_comments=0,
                avg_sentiment=0.0,
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
        
        # Trends by day
        trend_rows = (
            self.db.query(
                func.strftime("%Y-%m-%d", DataRecord.created_at).label("date"),
                func.count(DataRecord.id),
                func.sum(DataRecord.likes),
                func.sum(DataRecord.shares),
                func.sum(DataRecord.comments),
            )
            .filter(DataRecord.dataset_id == dataset_id)
            .group_by("date")
            .order_by("date")
            .all()
        )
        trends = [
            ActivityTrend(
                date=row[0],
                count=row[1] or 0,
                likes=row[2] or 0,
                shares=row[3] or 0,
                comments=row[4] or 0,
            )
            for row in trend_rows
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
        top_keywords = (
            [{"keyword": keyword, "count": count} for keyword, count in word_counter.most_common(10)]
            if word_counter
            else []
        )
        
        return AnalyticsSummary(
            dataset_id=dataset_id,
            total_records=len(records),
            sentiment=sentiment,
            total_likes=total_likes,
            total_shares=total_shares,
            total_comments=total_comments,
            avg_sentiment=avg_sentiment,
            trends=trends,
            top_keywords=top_keywords,
        )
