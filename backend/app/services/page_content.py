"""
页面内容服务。

负责提供案例详情和手册正文等页面级内容，
避免在路由层堆积过多文件读取和聚合逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paths import PROJECT_ROOT
from app.models.douyin import DouyinData
from app.models.task import Task
from app.models.weibo import WeiboData
from app.services.advanced_analyzer import get_advanced_analyzer
from app.services.data_processor import get_data_processor


MANUAL_PATH = PROJECT_ROOT / "网络舆情应对手册.md"


@dataclass(slots=True)
class ManualContent:
    title: str
    markdown: str
    source_path: str
    updated_at: str | None


class PageContentService:
    """聚合页面内容所需的真实数据。"""

    def load_manual_content(self) -> ManualContent:
        if not MANUAL_PATH.exists():
            raise FileNotFoundError(f"未找到手册文件: {MANUAL_PATH}")

        stat = MANUAL_PATH.stat()
        return ManualContent(
            title=MANUAL_PATH.stem,
            markdown=MANUAL_PATH.read_text(encoding="utf-8"),
            source_path=str(MANUAL_PATH),
            updated_at=None if stat.st_mtime is None else str(int(stat.st_mtime)),
        )

    async def get_case_detail(self, db: AsyncSession, case_id: int) -> dict[str, Any] | None:
        task = await db.scalar(select(Task).where(Task.id == case_id))
        if not task:
            return None

        if task.task_type == "douyin":
            rows = await db.execute(
                select(DouyinData)
                .where(DouyinData.task_id == task.id)
                .order_by(DouyinData.created_at.desc())
                .limit(1000)
            )
            data = rows.scalars().all()
            payload = [
                {
                    "user_name": item.author or "未知作者",
                    "user_id": item.author_id or "",
                    "content": item.content or item.title or "",
                    "publish_time": item.publish_time,
                    "like_count": item.like_count or 0,
                    "comment_count": item.comment_count or 0,
                    "share_count": item.share_count or 0,
                    "sentiment_label": item.sentiment_label or "neutral",
                    "platform": task.task_type,
                    "url": item.url or "",
                }
                for item in data
            ]
            recent_items = [
                {
                    "id": item.id,
                    "author": item.author or "未知作者",
                    "content": item.content or item.title or "",
                    "publish_time": item.publish_time.isoformat() if item.publish_time else None,
                    "likes": item.like_count or 0,
                    "comments": item.comment_count or 0,
                    "shares": item.share_count or 0,
                    "sentiment": item.sentiment_label or "neutral",
                    "url": item.url or "",
                }
                for item in data[:20]
            ]
        else:
            rows = await db.execute(
                select(WeiboData)
                .where(WeiboData.task_id == task.id)
                .order_by(WeiboData.created_at.desc())
                .limit(1000)
            )
            data = rows.scalars().all()
            payload = [
                {
                    "user_name": item.user_name or "未知作者",
                    "user_id": item.user_id or "",
                    "content": item.content or "",
                    "publish_time": item.publish_time,
                    "like_count": item.like_count or 0,
                    "comment_count": item.comment_count or 0,
                    "share_count": item.share_count or 0,
                    "sentiment_label": item.sentiment_label or "neutral",
                    "platform": task.task_type,
                    "url": item.url or "",
                }
                for item in data
            ]
            recent_items = [
                {
                    "id": item.id,
                    "author": item.user_name or "未知作者",
                    "content": item.content or "",
                    "publish_time": item.publish_time.isoformat() if item.publish_time else None,
                    "likes": item.like_count or 0,
                    "comments": item.comment_count or 0,
                    "shares": item.share_count or 0,
                    "sentiment": item.sentiment_label or "neutral",
                    "url": item.url or "",
                }
                for item in data[:20]
            ]

        processor = get_data_processor()
        analyzer = get_advanced_analyzer()
        statistics = processor.calculate_statistics(payload)
        risk = processor.calculate_risk_level(payload)

        topics = analyzer.simple_topic_clustering(
            [item["content"] for item in payload if item["content"]],
            n_topics=5,
            words_per_topic=8,
        ) if payload else []
        spreaders = analyzer.identify_key_spreaders(payload, top_n=8) if payload else []

        return {
            "id": task.id,
            "keyword": task.keyword,
            "task_type": task.task_type,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "statistics": statistics,
            "risk": risk,
            "topics": topics,
            "spreaders": spreaders,
            "recent_items": recent_items,
        }


_service = PageContentService()


def get_page_content_service() -> PageContentService:
    return _service
