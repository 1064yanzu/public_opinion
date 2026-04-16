"""
页面数据相关 API 路由
对应原项目的 views/page/page.py
"""
import os
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from app.dependencies import get_db, get_current_user, get_current_user_optional
from app.models.user import User
from app.models.weibo import WeiboData
from app.models.douyin import DouyinData
from app.models.hotspot import Hotspot
from app.models.task import Task
from app.config import settings
from app.services.wordcloud_generator import WordCloudGenerator
from app.services.page_content import get_page_content_service

router = APIRouter()

PROVINCE_ALIAS = {
    "北京市": "北京",
    "天津市": "天津",
    "上海市": "上海",
    "重庆市": "重庆",
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
    "黑龙江省": "黑龙江",
}


def _normalize_province_name(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    name = str(value).strip()
    if not name or name in {"未知", "N/A", "None", "nan"}:
        return None

    if name in PROVINCE_ALIAS:
        return PROVINCE_ALIAS[name]

    for suffix in ("省", "市", "壮族自治区", "回族自治区", "维吾尔自治区", "自治区", "特别行政区"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break

    return PROVINCE_ALIAS.get(name, name)


# ===== 请求/响应模型 =====
class ChartDataResponse(BaseModel):
    """图表数据响应"""
    heatmap_data: List[dict] = Field(default=[], description="热力图数据")
    sentiment_data: dict = Field(default={}, description="情感分布数据")
    gender_data: dict = Field(default={}, description="性别分布数据")


class HotTopicItem(BaseModel):
    """热点话题项"""
    title: str
    source: Optional[str] = None
    link: Optional[str] = None
    hot_value: Optional[int] = None


class RealtimeDataItem(BaseModel):
    """实时数据项"""
    author: str
    content: str
    link: Optional[str] = None
    author_url: Optional[str] = None
    publish_time: Optional[str] = None
    sentiment: Optional[str] = None


class SpiderSettingRequest(BaseModel):
    """爬虫设置请求"""
    keyword: str = Field(..., description="搜索关键词")
    platforms: List[str] = Field(..., description="平台列表")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    precision: str = Field(default="medium", description="精度")


class WordCloudRequest(BaseModel):
    """词云生成请求"""
    keyword: Optional[str] = None
    task_id: Optional[int] = None


# ===== 页面数据 API =====
@router.get("/home-data", summary="获取主页数据", description="异步加载主页展示数据")
async def get_home_data(db: AsyncSession = Depends(get_db)):
    """
    获取主页数据
    
    返回统计数据、最近微博数据和热点新闻
    """
    try:
        # 统计数据
        total_query = select(func.count()).select_from(WeiboData)
        total_result = await db.execute(total_query)
        total_count = total_result.scalar() or 0
        
        # 今日数据
        today = date.today()
        today_query = select(func.count()).select_from(WeiboData).where(
            func.date(WeiboData.created_at) == today
        )
        today_result = await db.execute(today_query)
        today_count = today_result.scalar() or 0
        
        # 情感统计
        positive_count = (await db.execute(
            select(func.count()).select_from(WeiboData).where(WeiboData.sentiment_label == "positive")
        )).scalar() or 0
        negative_count = (await db.execute(
            select(func.count()).select_from(WeiboData).where(WeiboData.sentiment_label == "negative")
        )).scalar() or 0
        neutral_count = (await db.execute(
            select(func.count()).select_from(WeiboData).where(WeiboData.sentiment_label == "neutral")
        )).scalar() or 0
        
        # 互动总量
        heat_query = select(
            func.sum(WeiboData.like_count + WeiboData.comment_count + WeiboData.share_count)
        )
        heat_result = await db.execute(heat_query)
        total_heat = heat_result.scalar() or 0
        
        # 最近数据
        recent_query = select(WeiboData).order_by(WeiboData.created_at.desc()).limit(20)
        recent_result = await db.execute(recent_query)
        recent_data = [
            {
                "author": item.user_name or "未知作者",
                "content": (item.content[:150] + "...") if item.content and len(item.content) > 150 else (item.content or "无内容"),
                "time": item.publish_time.strftime("%Y-%m-%d %H:%M") if item.publish_time else "未知时间",
                "shares": item.share_count,
                "comments": item.comment_count,
                "likes": item.like_count,
                "url": item.url or "#",
                "sentiment": item.sentiment_label or "neutral",
            }
            for item in recent_result.scalars().all()
        ]
        
        # 热点数据
        hotspot_query = select(Hotspot).order_by(Hotspot.publish_date.desc()).limit(10)
        hotspot_result = await db.execute(hotspot_query)
        hotspots = [
            {
                "title": h.title,
                "source": h.source,
                "link": h.link,
                "cover_image": h.cover_image,
            }
            for h in hotspot_result.scalars().all()
        ]
        
        return {
            "success": True,
            "data": {
                "unique_user_count": total_count,  # 用总数代替
                "total_heat_value": total_heat,
                "unique_ip_count": positive_count,  # 用正面数代替
                "row_count": total_count,
                "infos2_data": recent_data,
                "daily_hotspots": hotspots,
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "unique_user_count": 0,
                "total_heat_value": 0,
                "unique_ip_count": 0,
                "row_count": 0,
                "infos2_data": [],
                "daily_hotspots": [],
            }
        }


@router.get("/chart-data", response_model=ChartDataResponse, summary="获取图表数据",
            description="获取情感分布、地域分布等图表数据")
async def get_chart_data(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取图表数据
    
    - 热力图数据（地域分布）
    - 情感分布数据
    - 性别分布数据（如有）
    """
    weibo_query = select(WeiboData)
    douyin_query = select(DouyinData)
    if task_id:
        weibo_query = weibo_query.where(WeiboData.task_id == task_id)
        douyin_query = douyin_query.where(DouyinData.task_id == task_id)

    weibo_result = await db.execute(weibo_query.limit(1000))
    douyin_result = await db.execute(douyin_query.limit(1000))
    weibos = weibo_result.scalars().all()
    douyins = douyin_result.scalars().all()

    sentiment_counts = {"正面": 0, "负面": 0, "中性": 0}
    gender_data = {"男": 0, "女": 0, "未知": 0}
    province_counter = {}

    def consume_row(sentiment_label: Optional[str], gender: Optional[str], province: Optional[str]):
        if sentiment_label == "positive":
            sentiment_counts["正面"] += 1
        elif sentiment_label == "negative":
            sentiment_counts["负面"] += 1
        else:
            sentiment_counts["中性"] += 1

        gender_key = gender or "未知"
        if gender_key not in gender_data:
            gender_key = "未知"
        gender_data[gender_key] += 1

        province_name = _normalize_province_name(province)
        if province_name:
            province_counter[province_name] = province_counter.get(province_name, 0) + 1

    for item in weibos:
        consume_row(item.sentiment_label, item.gender, item.province)

    for item in douyins:
        consume_row(item.sentiment_label, item.gender, item.province)

    heatmap_data = [
        {"name": name, "value": count}
        for name, count in sorted(province_counter.items(), key=lambda entry: entry[1], reverse=True)
    ]
    
    return ChartDataResponse(
        heatmap_data=heatmap_data,
        sentiment_data=sentiment_counts,
        gender_data=gender_data,
    )


@router.get("/hot-topics", summary="获取热点话题", description="获取当前热点话题列表")
async def get_hot_topics(
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取热点话题"""
    query = select(Hotspot).order_by(Hotspot.publish_date.desc()).limit(limit)
    result = await db.execute(query)
    hotspots = result.scalars().all()
    
    if hotspots:
        return [
            {
                "title": h.title,
                "source": h.source,
                "link": h.link,
                "cover_image": h.cover_image,
                "publish_date": h.publish_date.isoformat() if h.publish_date else None,
            }
            for h in hotspots
        ]

    # 回退：如果数据库中尚未爬取热搜，执行实时获取（对齐旧版本功能）
    import aiohttp
    import logging
    try:
        url2 = 'https://www.douyin.com/aweme/v1/web/hot/search/list'
        headers = {
            'scheme':'https',
            'accept':'application/json, text/plain, */*',
            'referer':'https://www.douyin.com/hot',
            'sec-fetch-dest':'empty',
            'sec-fetch-mode':'cors',
            'sec-fetch-site':'same-origin',
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url2, headers=headers) as response:
                response.raise_for_status()
                json_data = await response.json()
                datas = json_data.get('data', {}).get('word_list', [])
                
                news = []
                for d in datas[:limit]:
                    word = d.get('word', '')
                    sentence_id = d.get('sentence_id', '')
                    video_url = f'https://www.douyin.com/hot?modal_id={sentence_id}'
                    news.append({
                        "title": word,
                        "source": "抖音热搜",
                        "link": video_url,
                        "cover_image": None,
                        "publish_date": None
                    })
                return news
    except Exception as e:
        logging.error(f"Failed to fetch realtime douyin hot topics: {e}")
        return []


@router.get("/realtime-monitoring", summary="获取实时监控数据",
            description="获取实时舆情监控数据")
async def get_realtime_monitoring(
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取实时监控数据"""
    query = select(WeiboData).order_by(WeiboData.created_at.desc()).limit(limit)
    result = await db.execute(query)
    data = result.scalars().all()
    
    return [
        {
            "author": item.user_name or "未知作者",
            "content": item.content or "无内容",
            "Link": item.url or "#",
            "authorUrl": item.url or "#",
        }
        for item in data
    ]


@router.get("/realtime-data", summary="获取实时数据", description="获取实时舆情分析数据")
async def get_realtime_data(
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取实时数据
    
    返回最新的舆情数据，支持关键词筛选
    """
    query = select(WeiboData)
    
    if keyword:
        query = query.where(WeiboData.content.contains(keyword))
    
    query = query.order_by(WeiboData.created_at.desc()).limit(limit)
    result = await db.execute(query)
    data = result.scalars().all()
    
    # 计算统计信息
    total = len(data)
    positive = sum(1 for d in data if d.sentiment_label == "positive")
    negative = sum(1 for d in data if d.sentiment_label == "negative")
    neutral = total - positive - negative
    
    return {
        "total": total,
        "sentiment_distribution": {
            "positive": round(positive / total * 100, 1) if total > 0 else 0,
            "negative": round(negative / total * 100, 1) if total > 0 else 0,
            "neutral": round(neutral / total * 100, 1) if total > 0 else 0,
        },
        "data": [
            {
                "id": item.id,
                "author": item.user_name or "未知作者",
                "content": item.content,
                "publish_time": item.publish_time.isoformat() if item.publish_time else None,
                "likes": item.like_count,
                "comments": item.comment_count,
                "shares": item.share_count,
                "sentiment": item.sentiment_label,
                "sentiment_score": item.sentiment_score,
                "url": item.url,
            }
            for item in data
        ],
    }


@router.get("/stats", summary="获取实时统计", description="获取实时统计数据")
async def get_stats(
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取实时统计数据"""
    base_query = select(func.count()).select_from(WeiboData)
    
    if task_id:
        base_query = base_query.where(WeiboData.task_id == task_id)
    
    total = (await db.execute(base_query)).scalar() or 0
    
    # 情感统计
    positive_query = base_query.where(WeiboData.sentiment_label == "positive")
    negative_query = base_query.where(WeiboData.sentiment_label == "negative")
    
    positive = (await db.execute(positive_query)).scalar() or 0
    negative = (await db.execute(negative_query)).scalar() or 0
    neutral = total - positive - negative
    
    # 互动统计
    interaction_query = select(
        func.sum(WeiboData.like_count).label("likes"),
        func.sum(WeiboData.comment_count).label("comments"),
        func.sum(WeiboData.share_count).label("shares"),
    )
    if task_id:
        interaction_query = interaction_query.where(WeiboData.task_id == task_id)
    
    interaction_result = await db.execute(interaction_query)
    interaction = interaction_result.first()
    
    return {
        "total_count": total,
        "sentiment": {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        },
        "interactions": {
            "likes": interaction.likes or 0 if interaction else 0,
            "comments": interaction.comments or 0 if interaction else 0,
            "shares": interaction.shares or 0 if interaction else 0,
        },
    }


@router.get("/status", summary="获取任务状态", description="获取当前系统任务状态")
async def get_status(db: AsyncSession = Depends(get_db)):
    """获取当前任务状态"""
    # 查询正在进行中的任务
    running_query = select(Task).where(Task.status == "processing")
    result = await db.execute(running_query)
    running_tasks = result.scalars().all()
    
    if running_tasks:
        task = running_tasks[0]
        return {
            "status": "working",
            "message": f"正在执行任务：{task.keyword}",
            "task_id": task.id,
            "progress": task.progress,
        }
    
    return {
        "status": "idle",
        "message": "系统空闲，可接受新任务",
    }


@router.post("/wordcloud", summary="生成词云", description="根据数据生成词云图片")
async def generate_wordcloud(
    request: WordCloudRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """生成词云"""
    # 获取文本数据
    query = select(WeiboData.content)
    
    if request.task_id:
        query = query.where(WeiboData.task_id == request.task_id)
    elif request.keyword:
        query = query.where(WeiboData.content.contains(request.keyword))
    
    query = query.limit(500)
    result = await db.execute(query)
    contents = [row[0] for row in result.all() if row[0]]
    
    if not contents:
        return {"image_url": "", "word_freq": {}, "message": "没有找到相关数据"}
    
    generator = WordCloudGenerator()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    image_path, word_freq = generator.generate(contents, filename=f"wordcloud_{timestamp}.png")

    return {
        "image_url": f"/static/wordcloud/{Path(image_path).name}" if image_path else "",
        "word_freq": dict(list(word_freq.items())[:100]),
        "message": "词云生成成功" if image_path else "词云图片生成失败，但词频统计成功",
    }


@router.get("/cases", summary="获取案例列表", description="获取舆情案例列表")
async def get_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取案例列表"""
    # 按关键词聚合任务作为案例
    query = select(Task).where(Task.status == "completed").order_by(Task.completed_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    count_query = select(func.count()).select_from(Task).where(Task.status == "completed")
    total = (await db.execute(count_query)).scalar() or 0
    
    return {
        "total": total,
        "cases": [
            {
                "id": t.id,
                "keyword": t.keyword,
                "type": t.task_type,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ],
    }


@router.get("/cases/{case_id}", summary="获取案例详情", description="基于已完成任务返回案例详情")
async def get_case_detail(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取单个案例详情。"""
    service = get_page_content_service()
    detail = await service.get_case_detail(db, case_id)

    if detail is None:
        raise HTTPException(status_code=404, detail="案例不存在")

    return detail


@router.get("/manual-content", summary="获取舆情应对手册内容", description="读取项目中的真实手册文档")
async def get_manual_content():
    """返回项目内置的舆情应对手册正文。"""
    service = get_page_content_service()
    content = service.load_manual_content()
    return {
        "title": content.title,
        "markdown": content.markdown,
        "source_path": content.source_path,
        "updated_at": content.updated_at,
    }


@router.get("/latest-data", summary="获取最新数据", description="获取最新爬取的数据")
async def get_latest_data(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取最新数据"""
    query = select(WeiboData).order_by(WeiboData.created_at.desc()).limit(limit)
    result = await db.execute(query)
    data = result.scalars().all()
    
    return [
        {
            "id": item.id,
            "content": item.content,
            "author": item.user_name,
            "publish_time": item.publish_time.isoformat() if item.publish_time else None,
            "likes": item.like_count,
            "comments": item.comment_count,
            "shares": item.share_count,
            "sentiment": item.sentiment_label,
        }
        for item in data
    ]
