"""
微博爬虫服务
基于原项目 spiders/articles_spider.py 的逻辑重写
"""
import re
import time
import random
import requests
import json
from urllib.parse import quote
from datetime import datetime
from typing import List, Dict, Optional, Any
from requests.cookies import create_cookie
from sqlalchemy.ext.asyncio import AsyncSession
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models.weibo import WeiboData
from app.models.task import Task
from app.config import settings


class WeiboSpider:
    """微博爬虫类"""
    
    BASE_URL = "https://m.weibo.cn/api/container/getIndex"
    SEARCH_URL = "https://m.weibo.cn/search"
    VISITOR_GEN_URL = "https://passport.weibo.com/visitor/genvisitor"
    VISITOR_INCAR_URL = "https://passport.weibo.com/visitor/visitor"
    
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    ]
    
    def __init__(self, cookie: str = ""):
        self.session = self._create_session()
        self.cookie = cookie or settings.WEIBO_COOKIE
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.last_error = ""
        self.visitor_initialized = False
    
    def _create_session(self) -> requests.Session:
        """创建优化的请求会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
            pool_block=False
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _seed_cookie(self, name: str, value: str):
        if not value:
            return
        for domain in (".weibo.com", ".weibo.cn", "m.weibo.cn", "passport.weibo.com"):
            self.session.cookies.set_cookie(create_cookie(name=name, value=value, domain=domain))

    def _seed_cookie_header(self):
        if not self.cookie:
            return
        for chunk in self.cookie.split(";"):
            if "=" not in chunk:
                continue
            name, value = chunk.split("=", 1)
            self._seed_cookie(name.strip(), value.strip())

    def _get_cookie_value(self, name: str) -> Optional[str]:
        for domain in ("m.weibo.cn", ".weibo.cn", ".weibo.com", "passport.weibo.com", None):
            try:
                if domain is None:
                    for cookie in self.session.cookies:
                        if cookie.name == name and cookie.value:
                            return cookie.value
                else:
                    value = self.session.cookies.get(name, domain=domain)
                    if value:
                        return value
            except Exception:
                continue
        return None

    def _prepare_visitor_session(self, keyword: str):
        if self.visitor_initialized:
            return
        if self.cookie:
            self._seed_cookie_header()
            self.visitor_initialized = True
            return

        callback = "gen_callback"
        response = self.session.get(
            f"{self.VISITOR_GEN_URL}?cb={callback}",
            headers={"User-Agent": random.choice(self.USER_AGENTS), "Referer": "https://weibo.com/"},
            timeout=30,
        )
        if response.status_code != 200 or "gen_callback(" not in response.text:
            raise RuntimeError(f"微博访客初始化失败，genvisitor 返回 HTTP {response.status_code}")

        match = re.search(r"gen_callback\((.*)\)", response.text)
        if not match:
            raise RuntimeError("微博访客初始化失败，无法解析 genvisitor 响应")

        data = json.loads(match.group(1))
        tid = data.get("data", {}).get("tid")
        if not tid:
            raise RuntimeError("微博访客初始化失败，未获取到 tid")

        incarnate = self.session.get(
            self.VISITOR_INCAR_URL,
            params={
                "a": "incarnate",
                "t": tid,
                "w": "2",
                "c": "095",
                "gc": "",
                "cb": "cross_domain",
                "from": "weibo",
                "_rand": str(time.time()),
            },
            headers={"User-Agent": random.choice(self.USER_AGENTS), "Referer": "https://weibo.com/"},
            timeout=30,
        )
        if incarnate.status_code != 200 or "cross_domain(" not in incarnate.text:
            raise RuntimeError(f"微博访客初始化失败，incarnate 返回 HTTP {incarnate.status_code}")

        match = re.search(r"cross_domain\((.*)\)", incarnate.text)
        if match:
            payload = json.loads(match.group(1))
            visitor_data = payload.get("data", {})
            self._seed_cookie("SUB", visitor_data.get("sub", ""))
            self._seed_cookie("SUBP", visitor_data.get("subp", ""))

        for cookie_name in ("SUB", "SUBP", "SVB", "SRT", "SRF"):
            cookie_value = self._get_cookie_value(cookie_name)
            if cookie_value:
                self._seed_cookie(cookie_name, cookie_value)

        self.session.get(
            self.SEARCH_URL,
            params={"containerid": f"100103type=1&q={keyword}"},
            headers={"User-Agent": random.choice(self.USER_AGENTS)},
            timeout=30,
        )

        self.visitor_initialized = True
    
    def _get_headers(self, keyword: str = "") -> Dict[str, str]:
        """获取随机请求头"""
        user_agent = random.choice(self.USER_AGENTS)
        encoded_keyword = quote(keyword, safe="") if keyword else ""
        referer = f'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{encoded_keyword}' if keyword else 'https://m.weibo.cn/'
        headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': referer,
            'X-Requested-With': 'XMLHttpRequest',
            'mweibo-pwa': '1',
            'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'priority': 'u=1, i',
        }
        xsrf = None
        for cookie_name in ('XSRF-TOKEN', 'SRF'):
            xsrf = self._get_cookie_value(cookie_name)
            if xsrf:
                break
        if xsrf:
            headers['x-xsrf-token'] = xsrf
        if self.cookie:
            headers['Cookie'] = self.cookie
        return headers
    
    @staticmethod
    def _trans_time(time_str: str) -> Optional[datetime]:
        """转换GMT时间为datetime对象"""
        if not time_str or time_str == 'N/A':
            return None
            
        try:
            GMT_FORMAT = '%a %b %d %H:%M:%S +0800 %Y'
            return datetime.strptime(time_str, GMT_FORMAT)
        except ValueError:
            pass
        
        # 尝试处理相对时间
        try:
            now = datetime.now()
            if "分钟前" in time_str:
                minutes = int(re.search(r'(\d+)', time_str).group(1))
                return now.replace(second=0, microsecond=0)
            elif "小时前" in time_str:
                return now.replace(minute=0, second=0, microsecond=0)
            elif "昨天" in time_str:
                return now.replace(hour=12, minute=0, second=0, microsecond=0)
            elif "今天" in time_str:
                return now.replace(second=0, microsecond=0)
        except:
            pass
        
        return None
    
    @staticmethod
    def _clean_content(text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        return re.sub(r'<[^>]+>', '', text).strip()
    
    def _process_mblog(self, mblog: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单条微博数据"""
        try:
            if not mblog:
                return None
            
            user = mblog.get('user', {}) or {}
            weibo_id = str(mblog.get('id', ''))
            bid = mblog.get('bid', '')
            
            # 获取用户性别
            gender = user.get('gender', '')
            if gender == 'm':
                gender = '男'
            elif gender == 'f':
                gender = '女'
            else:
                gender = '未知'
            
            return {
                'weibo_id': weibo_id,
                'content': self._clean_content(mblog.get('text', '')),
                'user_name': user.get('screen_name', '未知用户'),
                'user_id': str(user.get('id', '')),
                'publish_time': self._trans_time(mblog.get('created_at', '')),
                'like_count': mblog.get('attitudes_count', 0) or 0,
                'comment_count': mblog.get('comments_count', 0) or 0,
                'share_count': mblog.get('reposts_count', 0) or 0,
                'url': f"https://m.weibo.cn/detail/{bid}" if bid else None,
                'country': mblog.get('status_country', ''),
                'province': mblog.get('status_province', ''),
                'city': mblog.get('status_city', ''),
                'gender': gender,
            }
        except Exception as e:
            print(f"处理微博数据出错: {e}")
            return None
    
    def _crawl_page(self, keyword: str, page: int) -> List[Dict[str, Any]]:
        """爬取单页微博数据"""
        try:
            self._prepare_visitor_session(keyword)
            params = {
                "containerid": f"100103type=1&q={keyword}",
                "page_type": "searchall",
            }
            if page > 1:
                params["page"] = page
            
            self.request_count += 1
            
            response = self.session.get(
                self.BASE_URL,
                params=params,
                headers=self._get_headers(keyword),
                allow_redirects=False,
                timeout=30
            )
            
            if response.status_code == 302:
                self.last_error = "微博请求被重定向到访客/登录入口，当前 Cookie 未生效。请确认已点击保存配置，并重启当前桌面后端。"
                self.fail_count += 1
                return []

            if response.status_code != 200:
                print(f"页面 {page} 请求失败: HTTP {response.status_code}")
                if response.status_code == 432:
                    self.last_error = "微博接口返回 HTTP 432，当前请求已被风控拦截。请在设置页补充可用的微博 Cookie 后重试。"
                else:
                    self.last_error = f"微博接口请求失败，HTTP {response.status_code}"
                self.fail_count += 1
                return []
            
            data = response.json()
            
            if data.get("ok") == -100:
                self.last_error = "微博搜索接口当前要求登录态。自动访客态已完成，但官方仍返回 signin，请在设置页填写有效微博 Cookie。"
                self.fail_count += 1
                return []

            if not data or 'data' not in data:
                print(f"页面 {page} 数据格式异常")
                self.last_error = "微博接口返回数据格式异常，可能是登录态失效或请求被限制。"
                self.fail_count += 1
                return []
            
            cards = data.get('data', {}).get('cards', [])
            weibos = []
            
            for card in cards:
                card_type = card.get('card_type')
                
                if card_type == 9:
                    mblog = card.get('mblog', {})
                    weibo = self._process_mblog(mblog)
                    if weibo:
                        weibos.append(weibo)
                        
                elif card_type == 11:
                    card_group = card.get('card_group', [])
                    for sub_card in card_group:
                        if sub_card.get('card_type') == 9:
                            mblog = sub_card.get('mblog', {})
                            weibo = self._process_mblog(mblog)
                            if weibo:
                                weibos.append(weibo)
            
            self.success_count += 1
            print(f"页面 {page} 获取到 {len(weibos)} 条数据")
            return weibos
            
        except requests.exceptions.Timeout:
            print(f"页面 {page} 请求超时")
            self.last_error = "微博接口请求超时，请稍后重试。"
            self.fail_count += 1
            return []
        except RuntimeError as e:
            print(str(e))
            self.last_error = str(e)
            self.fail_count += 1
            return []
        except Exception as e:
            print(f"页面 {page} 爬取出错: {e}")
            self.last_error = f"微博爬取异常: {e}"
            self.fail_count += 1
            return []
    
    def search(self, keyword: str, max_page: int = 10) -> List[Dict[str, Any]]:
        """
        搜索微博
        
        Args:
            keyword: 搜索关键词
            max_page: 最大页数 (1-50)
            
        Returns:
            微博数据列表
        """
        print(f"开始爬取微博: keyword={keyword}, max_page={max_page}")
        
        # 限制最大页数
        max_page = min(max(max_page, 1), 50)
        
        all_weibos = []
        seen_ids = set()
        
        for page in range(1, max_page + 1):
            weibos = self._crawl_page(keyword, page)
            
            # 去重
            for weibo in weibos:
                weibo_id = weibo.get('weibo_id')
                if weibo_id and weibo_id not in seen_ids:
                    seen_ids.add(weibo_id)
                    all_weibos.append(weibo)
            
            # 延迟请求，避免被封
            if page < max_page:
                delay = random.uniform(0.5, 1.5)
                time.sleep(delay)
        
        print(f"爬取完成: 总计 {len(all_weibos)} 条数据, 成功 {self.success_count} 页, 失败 {self.fail_count} 页")
        return all_weibos
    
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
        
        # 同步爬取
        weibos = self.search(keyword, max_page)
        
        if not weibos:
            print("未获取到任何数据")
            raise RuntimeError(self.last_error or "微博未返回任何数据，请检查关键词或登录态。")
        
        # 情感分析
        analyzer = NLPAnalyzer()
        contents = [w.get('content', '') for w in weibos]
        sentiments = analyzer.batch_sentiment_analysis(contents)
        
        # 保存到数据库
        saved_count = 0
        for i, weibo in enumerate(weibos):
            try:
                sentiment = sentiments[i] if i < len(sentiments) else {'label': 'neutral', 'score': 0.5}
                
                weibo_data = WeiboData(
                    task_id=task.id,
                    weibo_id=weibo.get('weibo_id', ''),
                    content=weibo.get('content', ''),
                    user_name=weibo.get('user_name', ''),
                    user_id=weibo.get('user_id', ''),
                    publish_time=weibo.get('publish_time'),
                    like_count=weibo.get('like_count', 0),
                    comment_count=weibo.get('comment_count', 0),
                    share_count=weibo.get('share_count', 0),
                    url=weibo.get('url', ''),
                    gender=weibo.get('gender', ''),
                    province=weibo.get('province', ''),
                    city=weibo.get('city', ''),
                    country=weibo.get('country', ''),
                    sentiment_score=sentiment.get('score', 0.5),
                    sentiment_label=sentiment.get('label', 'neutral'),
                )
                db.add(weibo_data)
                saved_count += 1
            except Exception as e:
                print(f"保存微博数据出错: {e}")
                continue
        
        await db.commit()
        print(f"成功保存 {saved_count} 条数据到数据库")
        return saved_count


# 便捷函数
def crawl_weibo(keyword: str, max_page: int = 10) -> List[Dict[str, Any]]:
    """便捷的微博爬取函数"""
    spider = WeiboSpider()
    return spider.search(keyword, max_page)
