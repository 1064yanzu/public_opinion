"""
抖音爬虫服务
独立实现，不依赖原项目代码
"""
import time
import random
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.douyin import DouyinData
from app.models.task import Task
from app.config import settings


class DouyinSpider:
    """抖音爬虫类"""
    
    BASE_URL = "https://www.douyin.com/aweme/v1/web/search/item/"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "referer": "https://www.douyin.com/search/",
    }
    
    def __init__(self, cookie: str = ""):
        self.cookie = cookie or settings.DOUYIN_COOKIE
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp 会话"""
        if self.session is None or self.session.closed:
            headers = self.HEADERS.copy()
            if self.cookie:
                headers["cookie"] = self.cookie
            
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    @staticmethod
    def _trans_time(timestamp: int) -> Optional[datetime]:
        """转换时间戳"""
        try:
            if timestamp:
                return datetime.fromtimestamp(timestamp)
        except:
            pass
        return None
    
    @staticmethod
    def _format_duration(duration_ms: int) -> str:
        """格式化视频时长"""
        try:
            total_seconds = duration_ms // 1000
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}分{seconds}秒"
        except:
            return "未知"
    
    def _process_aweme(self, aweme_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单条抖音数据"""
        try:
            if not aweme_info:
                return None
            
            author = aweme_info.get('author', {}) or {}
            statistics = aweme_info.get('statistics', {}) or {}
            video = aweme_info.get('video', {}) or {}
            
            # 获取性别
            gender = author.get('gender', 0)
            if gender == 1:
                gender_text = '男'
            elif gender == 2:
                gender_text = '女'
            else:
                gender_text = '未知'
            
            video_id = str(aweme_info.get('aweme_id', ''))
            
            return {
                'video_id': video_id,
                'title': (aweme_info.get('desc', '') or '').strip().replace('\n', ' '),
                'content': (aweme_info.get('desc', '') or '').strip(),
                'author': author.get('nickname', '未知用户'),
                'author_id': str(author.get('uid', '')),
                'publish_time': self._trans_time(aweme_info.get('create_time', 0)),
                'like_count': statistics.get('digg_count', 0) or 0,
                'comment_count': statistics.get('comment_count', 0) or 0,
                'share_count': statistics.get('share_count', 0) or 0,
                'collect_count': statistics.get('collect_count', 0) or 0,
                'download_count': statistics.get('download_count', 0) or 0,
                'url': f"https://www.douyin.com/discover?modal_id={video_id}",
                'duration': self._format_duration(video.get('duration', 0)),
                'followers_count': author.get('follower_count', 0),
                'province': author.get('province', ''),
                'city': author.get('city', ''),
                'gender': gender_text,
                'verified': author.get('enterprise_verify_reason', ''),
            }
        except Exception as e:
            print(f"处理抖音数据出错: {e}")
            return None
    
    async def _crawl_page(self, keyword: str, offset: int, count: int = 16) -> tuple:
        """爬取单页抖音数据"""
        try:
            session = await self._get_session()
            
            params = {
                'aid': '6383',
                'channel': 'channel_pc_web',
                'search_channel': 'aweme_video_web',
                'enable_history': 1,
                'keyword': keyword,
                'query_correct_type': 1,
                'is_filter_search': 0,
                'offset': offset,
                'count': count,
                'need_filter_settings': 1,
                'list_type': 'single',
            }
            
            self.request_count += 1
            
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    print(f"抖音请求失败: HTTP {response.status}")
                    self.fail_count += 1
                    return [], False
                
                data = await response.json()
            
            if not data:
                self.fail_count += 1
                return [], False
            
            has_more = data.get('has_more', 0) == 1
            items = data.get('data', []) or []
            
            videos = []
            for item in items:
                aweme_info = item.get('aweme_info', {})
                video = self._process_aweme(aweme_info)
                if video:
                    videos.append(video)
            
            self.success_count += 1
            print(f"抖音 offset={offset} 获取到 {len(videos)} 条数据")
            return videos, has_more
            
        except asyncio.TimeoutError:
            print(f"抖音请求超时: offset={offset}")
            self.fail_count += 1
            return [], False
        except Exception as e:
            print(f"抖音爬取出错: {e}")
            self.fail_count += 1
            return [], False
    
    async def search(
        self,
        keyword: str,
        max_page: int = 5,
        delay_range: tuple = (1.5, 3.0)
    ) -> List[Dict[str, Any]]:
        """
        搜索抖音视频
        
        Args:
            keyword: 搜索关键词
            max_page: 最大页数 (1-20)
            delay_range: 请求延迟范围（秒）
            
        Returns:
            视频数据列表
        """
        print(f"开始爬取抖音: keyword={keyword}, max_page={max_page}")
        
        # 限制最大页数
        max_page = min(max(max_page, 1), 20)
        
        all_videos = []
        seen_ids = set()
        offset = 0
        count = 16
        
        try:
            for page in range(max_page):
                videos, has_more = await self._crawl_page(keyword, offset, count)
                
                # 去重
                for video in videos:
                    video_id = video.get('video_id')
                    if video_id and video_id not in seen_ids:
                        seen_ids.add(video_id)
                        all_videos.append(video)
                
                if not has_more:
                    print("没有更多数据")
                    break
                
                # 更新 offset
                offset += count
                count = 10  # 后续页面每页10条
                
                # 延迟请求
                if page < max_page - 1:
                    delay = random.uniform(*delay_range)
                    await asyncio.sleep(delay)
            
            print(f"抖音爬取完成: 总计 {len(all_videos)} 条数据")
            return all_videos
            
        finally:
            await self.close()
    
    async def search_and_save(
        self,
        keyword: str,
        max_page: int,
        task: Task,
        db: AsyncSession
    ) -> int:
        """
        搜索并保存到数据库
        
        Returns:
            保存的数据数量
        """
        from app.services.nlp_analyzer import NLPAnalyzer
        
        videos = await self.search(keyword, max_page)
        
        if not videos:
            return 0
        
        # 情感分析
        analyzer = NLPAnalyzer()
        contents = [v.get('content', '') or v.get('title', '') for v in videos]
        sentiments = analyzer.batch_sentiment_analysis(contents)
        
        # 保存到数据库
        saved_count = 0
        for i, video in enumerate(videos):
            try:
                sentiment = sentiments[i] if i < len(sentiments) else {'label': 'neutral', 'score': 0.5}
                
                douyin_data = DouyinData(
                    task_id=task.id,
                    video_id=video.get('video_id', ''),
                    title=video.get('title', ''),
                    content=video.get('content', ''),
                    author=video.get('author', ''),
                    author_id=video.get('author_id', ''),
                    publish_time=video.get('publish_time'),
                    like_count=video.get('like_count', 0),
                    comment_count=video.get('comment_count', 0),
                    share_count=video.get('share_count', 0),
                    url=video.get('url', ''),
                    followers_count=video.get('followers_count', 0),
                    province=video.get('province', ''),
                    city=video.get('city', ''),
                    gender=video.get('gender', ''),
                    sentiment_score=sentiment.get('score', 0.5),
                    sentiment_label=sentiment.get('label', 'neutral'),
                )
                db.add(douyin_data)
                saved_count += 1
            except Exception as e:
                print(f"保存抖音数据出错: {e}")
                continue
        
        await db.commit()
        return saved_count


# 便捷函数
async def crawl_douyin(keyword: str, max_page: int = 5, cookie: str = "") -> List[Dict[str, Any]]:
    """便捷的抖音爬取函数"""
    spider = DouyinSpider(cookie=cookie)
    return await spider.search(keyword, max_page)
