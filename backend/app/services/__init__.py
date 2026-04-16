"""
服务层模块
包含爬虫、NLP分析、词云生成等核心业务逻辑
"""
from app.services.weibo_spider import WeiboSpider, crawl_weibo
from app.services.douyin_spider import DouyinSpider, crawl_douyin
from app.services.nlp_analyzer import NLPAnalyzer, get_nlp_analyzer
from app.services.wordcloud_generator import WordCloudGenerator, generate_wordcloud
from app.services.advanced_analyzer import AdvancedAnalyzer, get_advanced_analyzer
from app.services.data_processor import DataProcessor, get_data_processor
from app.services.report_generator import ReportGenerator, generate_report
from app.services.page_content import PageContentService, get_page_content_service

__all__ = [
    # 爬虫
    "WeiboSpider",
    "DouyinSpider",
    "crawl_weibo",
    "crawl_douyin",
    # NLP
    "NLPAnalyzer",
    "get_nlp_analyzer",
    # 词云
    "WordCloudGenerator",
    "generate_wordcloud",
    # 高级分析
    "AdvancedAnalyzer",
    "get_advanced_analyzer",
    # 数据处理
    "DataProcessor",
    "get_data_processor",
    # 页面内容
    "PageContentService",
    "get_page_content_service",
    # 报告
    "ReportGenerator",
    "generate_report",
]
