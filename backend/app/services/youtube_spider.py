"""
YouTube 爬虫服务
通过 YouTube Data API v3 官方接口采集视频数据，独立实现，不依赖原项目代码。

与微博/抖音爬虫不同，YouTube 走官方 API：
  - 鉴权使用 API Key（在系统设置里配置 youtube_api_key），而非 Cookie。
  - search.list 负责关键词检索，videos.list 负责补全统计/时长等详情。
  - 每页固定 50 条，max_page 即检索页数。
配额说明：search.list 每次消耗 100 单位，videos.list 每次 1 单位，
单 Key 默认日配额 10000 单位（约 100 次关键词检索）。
"""
import re
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.youtube import YoutubeData
from app.models.task import Task
from app.config import settings


class YouTubeSpider:
    """YouTube 爬虫类（基于 YouTube Data API v3）"""

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    # search.list 每页最大 50；videos.list 每次最多 50 个 id
    PAGE_SIZE = 50
    DETAIL_BATCH = 50
    VIDEO_PART = "snippet,statistics,contentDetails"

    def __init__(self, api_key: str = ""):
        # 兼容运行时配置与环境变量两种来源
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.last_error: Optional[str] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp 会话"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=getattr(settings, "CRAWLER_TIMEOUT", 30))
            self.session = aiohttp.ClientSession(
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "User-Agent": "public-opinion-youtube/1.0 (gzip)",
                },
                timeout=timeout,
            )
        return self.session

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()

    # ── 工具方法 ─────────────────────────────────────────
    @staticmethod
    def _parse_publish_time(value: str) -> Optional[datetime]:
        """解析 ISO-8601 (RFC3339) 时间，例如 2024-01-02T03:04:05Z"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _parse_duration(iso_duration: str) -> str:
        """将 ISO-8601 时长（PT#H#M#S）格式化为 中文时长串"""
        if not iso_duration:
            return "未知"
        match = re.match(
            r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
            iso_duration,
        )
        if not match:
            return "未知"
        days, hours, minutes, seconds = (int(x) if x else 0 for x in match.groups())
        total_minutes = days * 24 * 60 + hours * 60 + minutes
        if total_minutes >= 60:
            return f"{total_minutes // 60}时{total_minutes % 60}分{seconds}秒"
        return f"{total_minutes}分{seconds}秒"

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    async def _api_get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """调用单个 YouTube Data API 端点，附带 API Key 与错误处理"""
        session = await self._get_session()
        query = dict(params)
        query["key"] = self.api_key
        self.request_count += 1

        try:
            async with session.get(f"{self.BASE_URL}/{endpoint}", params=query) as response:
                payload = await response.json(content_type=None)

                if response.status == 200:
                    self.success_count += 1
                    return payload

                self.fail_count += 1
                error = (payload or {}).get("error", {}) if isinstance(payload, dict) else {}
                errors = error.get("errors") or []
                reason = errors[0].get("reason") if errors else error.get("status", "")
                message = error.get("message", "") or f"HTTP {response.status}"

                if reason in ("quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"):
                    self.last_error = "YouTube API 配额已耗尽，请等待次日 PT 时区重置或更换 API Key。"
                elif reason in ("keyInvalid", "badRequest") or response.status in (400, 403):
                    self.last_error = f"YouTube API Key 无效或被拒绝（{reason or message}）。请到设置页检查 API Key。"
                else:
                    self.last_error = f"YouTube API 调用失败: HTTP {response.status} {reason} {message}".strip()

                print(f"YouTube API 错误: {self.last_error}")
                return None

        except asyncio.TimeoutError:
            self.fail_count += 1
            self.last_error = "YouTube API 请求超时。"
            print(self.last_error)
            return None
        except Exception as e:
            self.fail_count += 1
            self.last_error = f"YouTube API 请求异常: {e}"
            print(self.last_error)
            return None

    # ── 数据处理 ─────────────────────────────────────────
    def _process_video(self, video: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """将 videos.list 返回的单条视频转为统一字典"""
        try:
            video_id = video.get("id", "")
            if not video_id:
                return None

            snippet = video.get("snippet", {}) or {}
            statistics = video.get("statistics", {}) or {}
            content_details = video.get("contentDetails", {}) or {}

            title = (snippet.get("title", "") or "").strip()
            description = (snippet.get("description", "") or "").strip()

            return {
                "video_id": video_id,
                "title": title,
                # content 用于情感分析：标题 + 描述
                "content": (f"{title} {description}").strip() or title,
                "author": snippet.get("channelTitle", "未知频道"),
                "author_id": snippet.get("channelId", ""),
                "publish_time": self._parse_publish_time(snippet.get("publishedAt", "")),
                "like_count": self._to_int(statistics.get("likeCount")),
                "comment_count": self._to_int(statistics.get("commentCount")),
                "share_count": 0,  # YouTube 无转发概念
                "view_count": self._to_int(statistics.get("viewCount")),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": self._parse_duration(content_details.get("duration", "")),
                # YouTube 不提供发布者地域/性别，留空保持表结构一致
                "province": "",
                "city": "",
                "gender": "",
            }
        except Exception as e:
            print(f"处理 YouTube 数据出错: {e}")
            return None

    async def _search_video_ids(self, keyword: str, max_page: int) -> List[str]:
        """分页调用 search.list，收集去重后的视频 ID 列表"""
        video_ids: List[str] = []
        seen = set()
        next_token: Optional[str] = None

        for page in range(max_page):
            params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "maxResults": self.PAGE_SIZE,
                "order": "relevance",
                "safeSearch": "none",
            }
            if next_token:
                params["pageToken"] = next_token

            payload = await self._api_get("search", params)
            if not payload:
                break

            for item in payload.get("items", []):
                vid = (item.get("id", {}) or {}).get("videoId")
                if vid and vid not in seen:
                    seen.add(vid)
                    video_ids.append(vid)

            print(f"YouTube search 第 {page + 1} 页累计 {len(video_ids)} 个视频")

            next_token = payload.get("nextPageToken")
            if not next_token:
                break

            if page < max_page - 1:
                await asyncio.sleep(getattr(settings, "CRAWLER_DELAY", 1.0))

        return video_ids

    async def _fetch_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """按 50 个一批调用 videos.list 补全详情"""
        videos: List[Dict[str, Any]] = []
        for i in range(0, len(video_ids), self.DETAIL_BATCH):
            batch = video_ids[i:i + self.DETAIL_BATCH]
            payload = await self._api_get(
                "videos",
                {"part": self.VIDEO_PART, "id": ",".join(batch), "maxResults": self.DETAIL_BATCH},
            )
            if not payload:
                continue
            for video in payload.get("items", []):
                processed = self._process_video(video)
                if processed:
                    videos.append(processed)
        return videos

    async def search(self, keyword: str, max_page: int = 5) -> List[Dict[str, Any]]:
        """
        搜索 YouTube 视频

        Args:
            keyword: 搜索关键词
            max_page: 最大检索页数 (1-20)，每页 50 条

        Returns:
            视频数据列表
        """
        print(f"开始爬取 YouTube: keyword={keyword}, max_page={max_page}")

        if not self.api_key:
            self.last_error = "未配置 YouTube API Key，请到系统设置页填写后重试。"
            print(self.last_error)
            return []

        # search.list 配额较贵，限制最大页数
        max_page = min(max(max_page, 1), 20)

        try:
            video_ids = await self._search_video_ids(keyword, max_page)
            if not video_ids:
                print("YouTube 未检索到任何视频")
                return []

            videos = await self._fetch_video_details(video_ids)
            print(f"YouTube 爬取完成: 总计 {len(videos)} 条数据")
            return videos
        finally:
            await self.close()

    async def search_and_save(
        self,
        keyword: str,
        max_page: int,
        task: Task,
        db: AsyncSession,
    ) -> int:
        """
        搜索并保存到数据库

        Returns:
            保存的数据数量
        """
        from app.services.nlp_analyzer import NLPAnalyzer

        videos = await self.search(keyword, max_page)

        if not videos:
            raise RuntimeError(self.last_error or "YouTube 未返回任何数据，请检查关键词或 API Key。")

        # 情感分析（同步，通过 to_thread 移出事件循环避免阻塞其他请求）
        analyzer = NLPAnalyzer()
        contents = [v.get("content", "") or v.get("title", "") for v in videos]
        sentiments = await asyncio.to_thread(analyzer.batch_sentiment_analysis, contents)

        saved_count = 0
        for i, video in enumerate(videos):
            try:
                sentiment = sentiments[i] if i < len(sentiments) else {"label": "neutral", "score": 0.5}

                youtube_data = YoutubeData(
                    task_id=task.id,
                    video_id=video.get("video_id", ""),
                    title=video.get("title", ""),
                    content=video.get("content", ""),
                    author=video.get("author", ""),
                    author_id=video.get("author_id", ""),
                    publish_time=video.get("publish_time"),
                    like_count=video.get("like_count", 0),
                    comment_count=video.get("comment_count", 0),
                    share_count=video.get("share_count", 0),
                    view_count=video.get("view_count", 0),
                    url=video.get("url", ""),
                    duration=video.get("duration", ""),
                    province=video.get("province", ""),
                    city=video.get("city", ""),
                    gender=video.get("gender", ""),
                    sentiment_score=sentiment.get("score", 0.5),
                    sentiment_label=sentiment.get("label", "neutral"),
                )
                db.add(youtube_data)
                saved_count += 1
            except Exception as e:
                print(f"保存 YouTube 数据出错: {e}")
                continue

        await db.commit()
        print(f"成功保存 {saved_count} 条 YouTube 数据到数据库")
        return saved_count


# 便捷函数
async def crawl_youtube(keyword: str, max_page: int = 5, api_key: str = "") -> List[Dict[str, Any]]:
    """便捷的 YouTube 爬取函数"""
    spider = YouTubeSpider(api_key=api_key)
    return await spider.search(keyword, max_page)
