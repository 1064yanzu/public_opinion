"""Spider service for crawling social media data"""
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import time
import random
from abc import ABC, abstractmethod


class BaseSpider(ABC):
    """Base spider class for extensibility"""
    
    @abstractmethod
    def crawl(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """Crawl data from source"""
        pass
    
    @abstractmethod
    def parse_item(self, item: Dict) -> Optional[Dict]:
        """Parse single item"""
        pass


class WeiboSpider(BaseSpider):
    """Weibo spider implementation"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br"
        }
    
    def trans_time(self, v_str: str) -> str:
        """Convert GMT time to standard format"""
        try:
            GMT_FORMAT = '%a %b %d %H:%M:%S +0800 %Y'
            timearray = datetime.strptime(v_str, GMT_FORMAT)
            return timearray.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def crawl_page(self, keyword: str, page: int) -> List[Dict]:
        """Crawl single page"""
        try:
            url = 'https://m.weibo.cn/api/container/getIndex'
            params = {
                "containerid": f"100103type=1&q={keyword}",
                "page_type": "searchall",
                "page": page
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            cards = data.get("data", {}).get("cards", [])
            weibos = []
            
            for card in cards:
                if card.get('card_type') == 9:
                    mblog = card.get('mblog', {})
                    weibo_info = self.parse_item(mblog)
                    if weibo_info:
                        weibos.append(weibo_info)
                elif card.get('card_type') == 11:
                    card_group = card.get('card_group', [])
                    if card_group:
                        mblog = card_group[0].get('mblog', {})
                        weibo_info = self.parse_item(mblog)
                        if weibo_info:
                            weibos.append(weibo_info)
            
            return weibos
        except Exception as e:
            print(f"Error crawling page {page}: {str(e)}")
            return []
    
    def parse_item(self, mblog: Dict) -> Optional[Dict]:
        """Parse weibo item"""
        try:
            if not mblog:
                return None
            
            user = mblog.get('user', {})
            
            # Clean text
            text = mblog.get('text', '')
            import re
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'#[^#]+#', '', text)
            text = text.strip()
            
            return {
                'post_id': str(mblog.get('id', '')),
                'content': text,
                'author': user.get('screen_name', 'Unknown'),
                'publish_time': self.trans_time(mblog.get('created_at', '')),
                'likes': int(mblog.get('attitudes_count', 0)),
                'shares': int(mblog.get('reposts_count', 0)),
                'comments': int(mblog.get('comments_count', 0)),
            }
        except Exception as e:
            print(f"Error parsing item: {str(e)}")
            return None
    
    def crawl(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """Crawl multiple pages"""
        all_data = []
        
        for page in range(1, max_pages + 1):
            print(f"Crawling page {page}/{max_pages}...")
            page_data = self.crawl_page(keyword, page)
            all_data.extend(page_data)
            
            # Random delay to avoid being blocked
            if page < max_pages:
                time.sleep(random.uniform(1, 3))
        
        return all_data


class DouyinSpider(BaseSpider):
    """Douyin spider implementation (placeholder for now)"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def crawl(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """Crawl Douyin data"""
        # TODO: Implement Douyin spider
        # For now, return empty list or mock data
        print(f"Douyin spider not fully implemented yet for keyword: {keyword}")
        return []
    
    def parse_item(self, item: Dict) -> Optional[Dict]:
        """Parse Douyin item"""
        # TODO: Implement parsing
        return None


class SpiderFactory:
    """Factory for creating spider instances"""
    
    _spiders = {
        'weibo': WeiboSpider,
        'douyin': DouyinSpider,
    }
    
    @classmethod
    def create(cls, source: str) -> BaseSpider:
        """Create spider instance by source name"""
        spider_class = cls._spiders.get(source.lower())
        if not spider_class:
            raise ValueError(f"Unknown spider source: {source}")
        return spider_class()
    
    @classmethod
    def register_spider(cls, name: str, spider_class: type):
        """Register a new spider type (for extensibility)"""
        cls._spiders[name.lower()] = spider_class
    
    @classmethod
    def list_sources(cls) -> List[str]:
        """List available spider sources"""
        return list(cls._spiders.keys())


class SpiderService:
    """High-level spider service"""
    
    def __init__(self):
        self.factory = SpiderFactory()
    
    def crawl_data(self, source: str, keyword: str, max_pages: int = 5) -> List[Dict]:
        """
        Crawl data from specified source
        
        Args:
            source: Data source (weibo, douyin, etc.)
            keyword: Search keyword
            max_pages: Maximum pages to crawl
            
        Returns:
            List of parsed data records
        """
        try:
            spider = self.factory.create(source)
            return spider.crawl(keyword, max_pages)
        except Exception as e:
            print(f"Error in spider service: {str(e)}")
            return []
    
    def available_sources(self) -> List[str]:
        """Get list of available sources"""
        return self.factory.list_sources()
