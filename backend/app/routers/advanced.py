"""
高级分析 API 路由
包含关键传播主体识别、主题聚类、趋势分析等功能
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.dependencies import get_db, get_current_user_optional
from app.models.weibo import WeiboData
from app.models.douyin import DouyinData
from app.models.user import User

router = APIRouter()


# ===== 请求/响应模型 =====
class KeySpreaderResponse(BaseModel):
    """关键传播主体响应"""
    user_name: str
    user_id: str
    post_count: int
    total_likes: int
    total_comments: int
    total_shares: int
    followers: int
    avg_interaction: float
    influence_score: float


class TopicResponse(BaseModel):
    """主题响应"""
    topic_id: int
    keywords: List[str]
    doc_count: int
    doc_ratio: float


class TrendPointResponse(BaseModel):
    """趋势数据点"""
    time: str
    count: int
    likes: int
    comments: int
    shares: int
    positive: int
    negative: int


# ===== API 路由 =====
@router.get("/key-spreaders", summary="关键传播主体识别",
            description="识别数据中最具影响力的传播主体")
async def get_key_spreaders(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    top_n: int = Query(20, ge=1, le=100, description="返回数量"),
    platform: str = Query("weibo", description="平台：weibo/douyin"),
    db: AsyncSession = Depends(get_db)
):
    """
    识别关键传播主体
    
    基于多维度评估用户的传播影响力：
    - 互动量（点赞、评论、转发）
    - 发布频率
    - 内容质量（平均互动量）
    - 粉丝量
    """
    from app.services.advanced_analyzer import get_advanced_analyzer
    
    # 查询数据
    if platform == "douyin":
        query = select(DouyinData)
        if task_id:
            query = query.where(DouyinData.task_id == task_id)
        if keyword:
            query = query.where(DouyinData.content.contains(keyword))
    else:
        query = select(WeiboData)
        if task_id:
            query = query.where(WeiboData.task_id == task_id)
        if keyword:
            query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(1000)  # 限制数据量
    result = await db.execute(query)
    data = result.scalars().all()
    
    if not data:
        return {"spreaders": [], "total": 0}
    
    # 转换为字典列表
    data_list = []
    for item in data:
        if platform == "douyin":
            data_list.append({
                'user_name': item.author,
                'user_id': item.author_id,
                'like_count': item.like_count,
                'comment_count': item.comment_count,
                'share_count': item.share_count,
                'followers_count': 0,
            })
        else:
            data_list.append({
                'user_name': item.user_name,
                'user_id': item.user_id,
                'like_count': item.like_count,
                'comment_count': item.comment_count,
                'share_count': item.share_count,
                'followers_count': 0,
            })
    
    # 分析
    analyzer = get_advanced_analyzer()
    spreaders = analyzer.identify_key_spreaders(data_list, top_n)
    
    return {
        "spreaders": spreaders,
        "total": len(spreaders),
        "data_count": len(data_list),
    }


@router.get("/topics", summary="主题聚类分析",
            description="对文本进行主题聚类，识别主要话题")
async def get_topics(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    n_topics: int = Query(5, ge=2, le=10, description="主题数量"),
    words_per_topic: int = Query(10, ge=5, le=20, description="每个主题的关键词数"),
    db: AsyncSession = Depends(get_db)
):
    """
    主题聚类分析
    
    使用简化的主题模型对文本进行聚类，
    识别数据中的主要话题和关键词
    """
    from app.services.advanced_analyzer import get_advanced_analyzer
    
    # 查询数据
    query = select(WeiboData.content)
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(500)
    result = await db.execute(query)
    texts = [row[0] for row in result.all() if row[0]]
    
    if not texts:
        return {"topics": [], "total_docs": 0}
    
    # 分析
    analyzer = get_advanced_analyzer()
    topics = analyzer.simple_topic_clustering(texts, n_topics, words_per_topic)
    
    return {
        "topics": topics,
        "total_docs": len(texts),
    }


@router.get("/trend", summary="趋势分析",
            description="分析数据随时间的变化趋势")
async def get_trend(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    interval: str = Query("day", description="时间间隔：hour/day/week"),
    db: AsyncSession = Depends(get_db)
):
    """
    趋势分析
    
    分析数据量、互动量、情感随时间的变化趋势
    """
    from app.services.advanced_analyzer import get_advanced_analyzer
    
    # 查询数据
    query = select(WeiboData)
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(1000)
    result = await db.execute(query)
    data = result.scalars().all()
    
    if not data:
        return {"timeline": [], "stats": {}}
    
    # 转换数据
    data_list = [
        {
            'publish_time': item.publish_time,
            'like_count': item.like_count,
            'comment_count': item.comment_count,
            'share_count': item.share_count,
            'sentiment_label': item.sentiment_label,
        }
        for item in data
    ]
    
    # 分析
    analyzer = get_advanced_analyzer()
    trend = analyzer.analyze_trend(data_list, interval=interval)
    
    return trend


@router.get("/geography", summary="地域分析",
            description="分析数据的地域分布")
async def get_geography(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    地域分析
    
    分析数据的地域分布和各地区的情感倾向
    """
    from app.services.advanced_analyzer import get_advanced_analyzer
    
    # 注：需要数据中有省份字段，这里用模拟数据演示
    # 实际使用时需要根据数据结构调整
    
    return {
        "provinces": [],
        "message": "地域分析需要数据中包含省份信息",
    }


@router.get("/sentiment-evolution", summary="情感演化分析",
            description="分析情感随时间的变化趋势")
async def get_sentiment_evolution(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    情感演化分析
    
    分析正面/负面/中性情感随时间的变化
    """
    from app.services.advanced_analyzer import get_advanced_analyzer
    
    # 查询数据
    query = select(WeiboData)
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(1000)
    result = await db.execute(query)
    data = result.scalars().all()
    
    if not data:
        return {"evolution": [], "trend_direction": "insufficient_data"}
    
    # 转换数据
    data_list = [
        {
            'publish_time': item.publish_time,
            'sentiment_label': item.sentiment_label,
        }
        for item in data
    ]
    
    # 分析
    analyzer = get_advanced_analyzer()
    evolution = analyzer.analyze_sentiment_evolution(data_list)
    
    return evolution


@router.get("/keyword-comparison", summary="正负面关键词对比",
            description="对比正面和负面文本的关键词差异")
async def get_keyword_comparison(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    top_n: int = Query(15, ge=5, le=30, description="每类返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    正负面关键词对比
    
    分析正面和负面文本中的差异化关键词
    """
    from app.services.advanced_analyzer import get_advanced_analyzer
    
    # 查询正面数据
    pos_query = select(WeiboData.content).where(WeiboData.sentiment_label == "positive")
    neg_query = select(WeiboData.content).where(WeiboData.sentiment_label == "negative")
    
    if task_id:
        pos_query = pos_query.where(WeiboData.task_id == task_id)
        neg_query = neg_query.where(WeiboData.task_id == task_id)
    if keyword:
        pos_query = pos_query.where(WeiboData.content.contains(keyword))
        neg_query = neg_query.where(WeiboData.content.contains(keyword))
    
    pos_result = await db.execute(pos_query.limit(300))
    neg_result = await db.execute(neg_query.limit(300))
    
    positive_texts = [row[0] for row in pos_result.all() if row[0]]
    negative_texts = [row[0] for row in neg_result.all() if row[0]]
    
    if not positive_texts and not negative_texts:
        return {"positive": [], "negative": [], "common": []}
    
    # 分析
    analyzer = get_advanced_analyzer()
    comparison = analyzer.compare_keywords(positive_texts, negative_texts, top_n)
    
    # 转换格式
    return {
        "positive": [{"word": w, "count": c} for w, c in comparison['positive']],
        "negative": [{"word": w, "count": c} for w, c in comparison['negative']],
        "common": [{"word": w, "count": c} for w, c in comparison['common']],
        "positive_count": len(positive_texts),
        "negative_count": len(negative_texts),
    }


@router.post("/wordcloud", summary="生成词云",
             description="根据数据生成词云图片")
async def generate_wordcloud(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    max_words: int = Query(200, ge=50, le=500, description="最大词数"),
    db: AsyncSession = Depends(get_db)
):
    """
    生成词云
    
    根据文本数据生成词云图片和词频统计
    """
    from app.services.wordcloud_generator import WordCloudGenerator
    
    # 查询数据
    query = select(WeiboData.content)
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(500)
    result = await db.execute(query)
    texts = [row[0] for row in result.all() if row[0]]
    
    if not texts:
        return {"image_url": None, "word_freq": {}, "message": "没有找到数据"}
    
    # 生成词云
    generator = WordCloudGenerator()
    image_path, word_freq = generator.generate(texts, max_words=max_words)
    
    # 生成 URL
    if image_path:
        image_url = f"/static/wordcloud/{image_path.split('/')[-1]}"
    else:
        image_url = None
    
    return {
        "image_url": image_url,
        "word_freq": dict(list(word_freq.items())[:100]),  # 只返回前100个
        "total_words": len(word_freq),
        "message": "词云生成成功" if image_path else "词云图片生成失败，但词频统计成功",
    }


@router.get("/risk-assessment", summary="风险评估",
            description="基于多维度评估舆情风险等级")
async def get_risk_assessment(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    风险评估
    
    基于以下维度评估风险：
    - 负面情感占比
    - 互动热度
    - 传播速度
    """
    from app.services.data_processor import get_data_processor
    
    # 查询数据
    query = select(WeiboData)
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(1000)
    result = await db.execute(query)
    data = result.scalars().all()
    
    if not data:
        return {"level": "低", "score": 0, "factors": [], "message": "没有找到数据"}
    
    # 转换数据
    data_list = [
        {
            'content': item.content,
            'like_count': item.like_count,
            'comment_count': item.comment_count,
            'share_count': item.share_count,
            'sentiment_label': item.sentiment_label,
            'publish_time': item.publish_time,
        }
        for item in data
    ]
    
    # 风险评估
    processor = get_data_processor()
    risk_info = processor.calculate_risk_level(data_list)
    
    return risk_info


@router.post("/report", summary="生成分析报告",
             description="生成完整的舆情分析报告")
async def generate_analysis_report(
    keyword: str = Query(..., description="分析关键词"),
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    生成分析报告
    
    生成包含以下内容的完整报告：
    - 数据概览
    - 情感分析
    - 风险评估
    - 主题分析
    - 关键传播主体
    - 建议与对策
    """
    from app.services.data_processor import get_data_processor
    from app.services.advanced_analyzer import get_advanced_analyzer
    from app.services.report_generator import ReportGenerator
    
    # 查询数据
    query = select(WeiboData)
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(1000)
    result = await db.execute(query)
    data = result.scalars().all()
    
    if not data:
        return {"success": False, "message": "没有找到数据"}
    
    # 转换数据
    data_list = [
        {
            'user_name': item.user_name,
            'content': item.content,
            'like_count': item.like_count,
            'comment_count': item.comment_count,
            'share_count': item.share_count,
            'sentiment_label': item.sentiment_label,
            'publish_time': item.publish_time,
        }
        for item in data
    ]
    
    # 获取统计信息
    processor = get_data_processor()
    statistics = processor.calculate_statistics(data_list)
    risk_info = processor.calculate_risk_level(data_list)
    
    # 获取主题和传播主体
    analyzer = get_advanced_analyzer()
    texts = [d['content'] for d in data_list if d['content']]
    topics = analyzer.simple_topic_clustering(texts, n_topics=5)
    key_spreaders = analyzer.identify_key_spreaders(data_list, top_n=10)
    
    # 生成报告
    generator = ReportGenerator()
    report_info = generator.generate_and_save(
        keyword=keyword,
        data=data_list,
        statistics=statistics,
        risk_info=risk_info,
        topics=topics,
        key_spreaders=key_spreaders,
    )
    
    return {
        "success": True,
        "download_url": report_info['download_url'],
        "filename": report_info['filename'],
        "statistics": statistics,
        "risk_info": risk_info,
    }


@router.get("/statistics", summary="获取综合统计",
            description="获取数据的综合统计信息")
async def get_statistics(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取综合统计信息
    
    包括数据量、互动量、情感分布、性别分布、地域分布等
    """
    from app.services.data_processor import get_data_processor
    
    # 查询数据
    query = select(WeiboData)
    if task_id:
        query = query.where(WeiboData.task_id == task_id)
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.limit(1000)
    result = await db.execute(query)
    data = result.scalars().all()
    
    if not data:
        return {"total_count": 0, "message": "没有找到数据"}
    
    # 转换数据
    data_list = [
        {
            'like_count': item.like_count,
            'comment_count': item.comment_count,
            'share_count': item.share_count,
            'sentiment_label': item.sentiment_label,
            'gender': '未知',  # 如果有性别字段可以添加
            'province': '未知',  # 如果有省份字段可以添加
            'platform': 'weibo',
        }
        for item in data
    ]
    
    processor = get_data_processor()
    statistics = processor.calculate_statistics(data_list)
    
    return statistics
