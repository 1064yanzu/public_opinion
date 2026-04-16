"""
数据分析相关 API 路由
"""
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from app.dependencies import get_db, get_current_user_optional
from app.models.user import User
from app.models.weibo import WeiboData
from app.models.douyin import DouyinData
from app.models.hotspot import Hotspot
from app.services.wordcloud_generator import WordCloudGenerator
from app.schemas import (
    StatsResponse, SentimentDistribution, HomeDataResponse,
    SentimentRequest, SentimentResponse, SentimentResult,
    WordCloudResponse, ReportRequest, ReportResponse, MessageResponse
)

router = APIRouter()


@router.get("/home", response_model=HomeDataResponse, summary="获取主页数据",
            description="获取主页展示所需的统计数据、情感分布和最近数据")
async def get_home_data(db: AsyncSession = Depends(get_db)):
    """
    获取主页数据
    
    包括：
    - 数据统计（总数、今日新增、情感分布）
    - 最近爬取的数据
    - 热点新闻
    """
    # 统计微博数据
    weibo_total = await db.execute(select(func.count()).select_from(WeiboData))
    weibo_count = weibo_total.scalar() or 0
    
    # 今日新增
    today = date.today()
    today_query = select(func.count()).select_from(WeiboData).where(
        func.date(WeiboData.created_at) == today
    )
    today_result = await db.execute(today_query)
    today_count = today_result.scalar() or 0
    
    # 情感统计
    positive_query = select(func.count()).select_from(WeiboData).where(WeiboData.sentiment_label == "positive")
    negative_query = select(func.count()).select_from(WeiboData).where(WeiboData.sentiment_label == "negative")
    neutral_query = select(func.count()).select_from(WeiboData).where(WeiboData.sentiment_label == "neutral")
    
    positive_count = (await db.execute(positive_query)).scalar() or 0
    negative_count = (await db.execute(negative_query)).scalar() or 0
    neutral_count = (await db.execute(neutral_query)).scalar() or 0
    
    # 计算情感分布百分比
    total_sentiment = positive_count + negative_count + neutral_count
    if total_sentiment > 0:
        sentiment_dist = SentimentDistribution(
            positive=round(positive_count / total_sentiment * 100, 1),
            negative=round(negative_count / total_sentiment * 100, 1),
            neutral=round(neutral_count / total_sentiment * 100, 1)
        )
    else:
        sentiment_dist = SentimentDistribution(positive=0, negative=0, neutral=100)
    
    # 最近数据（限制20条）
    recent_query = select(WeiboData).order_by(WeiboData.created_at.desc()).limit(20)
    recent_result = await db.execute(recent_query)
    recent_data = [
        {
            "id": item.id,
            "content": item.content[:100] if item.content else "",
            "user_name": item.user_name,
            "publish_time": item.publish_time.isoformat() if item.publish_time else None,
            "sentiment": item.sentiment_label,
            "like_count": item.like_count,
        }
        for item in recent_result.scalars().all()
    ]
    
    # 热点数据
    hotspot_query = select(Hotspot).order_by(Hotspot.publish_date.desc()).limit(10)
    hotspot_result = await db.execute(hotspot_query)
    hotspots = [
        {
            "id": h.id,
            "title": h.title,
            "source": h.source,
            "link": h.link,
            "cover_image": h.cover_image,
        }
        for h in hotspot_result.scalars().all()
    ]
    
    return HomeDataResponse(
        stats=StatsResponse(
            total_count=weibo_count,
            today_count=today_count,
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
        ),
        sentiment_distribution=sentiment_dist,
        recent_data=recent_data,
        hotspots=hotspots,
    )


@router.get("/stats", response_model=StatsResponse, summary="获取统计数据",
            description="获取数据统计信息")
async def get_stats(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取数据统计"""
    base_query = select(func.count()).select_from(WeiboData)
    
    if task_id:
        base_query = base_query.where(WeiboData.task_id == task_id)
    
    total_count = (await db.execute(base_query)).scalar() or 0
    
    # 今日新增
    today = date.today()
    today_query = base_query.where(func.date(WeiboData.created_at) == today)
    today_count = (await db.execute(today_query)).scalar() or 0
    
    # 情感统计
    positive_query = base_query.where(WeiboData.sentiment_label == "positive")
    negative_query = base_query.where(WeiboData.sentiment_label == "negative")
    neutral_query = base_query.where(WeiboData.sentiment_label == "neutral")
    
    positive_count = (await db.execute(positive_query)).scalar() or 0
    negative_count = (await db.execute(negative_query)).scalar() or 0
    neutral_count = (await db.execute(neutral_query)).scalar() or 0
    
    return StatsResponse(
        total_count=total_count,
        today_count=today_count,
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count,
    )


@router.post("/sentiment", response_model=SentimentResponse, summary="情感分析",
             description="对给定文本进行情感分析")
async def analyze_sentiment(request: SentimentRequest):
    """
    批量情感分析
    
    - **texts**: 待分析的文本列表
    
    返回每个文本的情感标签和分数
    """
    results = []
    
    for text in request.texts:
        try:
            # 使用 SnowNLP 进行情感分析
            from snownlp import SnowNLP
            s = SnowNLP(text)
            score = s.sentiments
            
            if score > 0.6:
                sentiment = "positive"
            elif score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            results.append(SentimentResult(
                text=text,
                sentiment=sentiment,
                score=round(score, 4)
            ))
        except Exception as e:
            # 分析失败时返回中性
            results.append(SentimentResult(
                text=text,
                sentiment="neutral",
                score=0.5
            ))
    
    return SentimentResponse(results=results)


@router.post("/wordcloud", response_model=WordCloudResponse, summary="生成词云",
             description="根据关键词生成词云图片")
async def generate_wordcloud(
    keyword: str = Query(..., description="关键词"),
    task_id: Optional[int] = Query(None, description="任务ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    生成词云
    
    - **keyword**: 分析关键词
    - **task_id**: 可选的任务ID筛选
    
    返回词云图片URL和词频统计
    """
    # 查询相关数据
    query = select(WeiboData.content)
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
    else:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(500)  # 限制数量
    result = await db.execute(query)
    contents = [row[0] for row in result.all() if row[0]]
    
    if not contents:
        return WordCloudResponse(image_url="", word_freq={})
    
    generator = WordCloudGenerator()
    image_path, word_freq = generator.generate(
        contents,
        filename=f"{keyword}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png",
    )

    return WordCloudResponse(
        image_url=f"/static/wordcloud/{Path(image_path).name}" if image_path else "",
        word_freq=dict(list(word_freq.items())[:100]),
    )


@router.post("/report", response_model=ReportResponse, summary="生成报告",
             description="根据关键词生成分析报告")
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    生成分析报告
    
    - **keyword**: 分析关键词
    - **report_type**: 报告类型（comprehensive/sentiment/trend）
    
    返回报告ID和内容
    """
    import uuid
    
    report_id = f"report_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
    
    # 获取数据统计
    query = select(WeiboData).where(WeiboData.content.contains(request.keyword)).limit(100)
    result = await db.execute(query)
    data = result.scalars().all()
    
    total_count = len(data)
    positive_count = sum(1 for d in data if d.sentiment_label == "positive")
    negative_count = sum(1 for d in data if d.sentiment_label == "negative")
    neutral_count = total_count - positive_count - negative_count
    
    content = {
        "title": f"{request.keyword}舆情分析报告",
        "summary": f"共分析 {total_count} 条相关数据",
        "sentiment_distribution": {
            "positive": round(positive_count / total_count * 100, 1) if total_count > 0 else 0,
            "neutral": round(neutral_count / total_count * 100, 1) if total_count > 0 else 0,
            "negative": round(negative_count / total_count * 100, 1) if total_count > 0 else 0,
        },
        "key_topics": [],  # TODO: 提取关键话题
    }
    
    return ReportResponse(
        report_id=report_id,
        status="completed",
        download_url=f"/api/analysis/report/download/{report_id}",
        content=content,
    )
