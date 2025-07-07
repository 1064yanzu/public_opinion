import os.path
import re
from jsonpath import jsonpath
import requests
import pandas as pd
from datetime import datetime
import os
import time
import random
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.common import get_persistent_file_path, get_temp_file_path, update_persistent_file
from utils.network_optimizer import optimized_spider_request, batch_spider_requests, spider_optimizer
from utils.async_task_manager import task_manager
from utils.performance_monitor import monitor_performance
from utils.cache_manager import cached, memory_cleanup
from config.settings import PERFORMANCE_CONFIG
def trans_time(v_str):
    try:
        """转换GMT时间为标准格式"""
        GMT_FORMAT = '%a %b %d %H:%M:%S +0800 %Y'
        timearray = datetime.strptime(v_str, GMT_FORMAT)
        ret_time = timearray.strftime("%Y-%m-%d %H:%M:%S")
        return ret_time
    except ValueError:
        # 如果转换失败，则返回默认值
        return 'N/A'

@monitor_performance('crawl_weibo_page')
def crawl_weibo_page(keyword, page):
    """
    爬取单页微博数据（优化版本）
    :param keyword: 关键词
    :param page: 页码
    :return: 数据列表
    """
    try:
        url = 'https://m.weibo.cn/api/container/getIndex'
        params = {
            "containerid": f"100103type=1&q={keyword}",
            "page_type": "searchall",
            "page": page
        }

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br"
        }

        # 使用优化的网络请求
        response_data = optimized_spider_request(url, params=params, headers=headers)

        if not response_data or 'data' not in response_data:
            print(f"页面 {page} 数据获取失败")
            return []

        cards = response_data["data"].get("cards", [])

        weibos = []
        for card in cards:
            if card.get('card_type') == 9:
                mblog = card.get('mblog', {})
                weibo_info = process_weibo_data(mblog)
                if weibo_info:
                    weibos.append(weibo_info)
            elif card.get('card_type') == 11:
                card_group = card.get('card_group', [])
                if card_group:
                    mblog = card_group[0].get('mblog', {})
                    weibo_info = process_weibo_data(mblog)
                    if weibo_info:
                        weibos.append(weibo_info)

        print(f"页面 {page} 获取到 {len(weibos)} 条数据")
        return weibos

    except Exception as e:
        print(f"爬取微博页面时出错: {str(e)}")
        return []


def crawl_weibo_pages_batch(keyword, pages):
    """
    批量爬取微博页面（并发版本）
    :param keyword: 关键词
    :param pages: 页码列表
    :return: 所有数据列表
    """
    print(f"开始批量爬取微博数据: 关键词={keyword}, 页数={len(pages)}")

    # 准备批量请求
    requests_list = []
    for page in pages:
        url = 'https://m.weibo.cn/api/container/getIndex'
        params = {
            "containerid": f"100103type=1&q={keyword}",
            "page_type": "searchall",
            "page": page
        }
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br"
        }
        requests_list.append({
            'url': url,
            'params': params,
            'headers': headers
        })

    # 批量请求
    max_workers = min(len(pages), PERFORMANCE_CONFIG.get('max_workers', 3))
    responses = batch_spider_requests(requests_list, max_workers=max_workers)

    # 处理响应
    all_weibos = []
    for i, response_data in enumerate(responses):
        if not response_data or 'data' not in response_data:
            print(f"页面 {pages[i]} 数据获取失败")
            continue

        cards = response_data["data"].get("cards", [])
        page_weibos = []

        for card in cards:
            if card.get('card_type') == 9:
                mblog = card.get('mblog', {})
                weibo_info = process_weibo_data(mblog)
                if weibo_info:
                    page_weibos.append(weibo_info)
            elif card.get('card_type') == 11:
                card_group = card.get('card_group', [])
                if card_group:
                    mblog = card_group[0].get('mblog', {})
                    weibo_info = process_weibo_data(mblog)
                    if weibo_info:
                        page_weibos.append(weibo_info)

        all_weibos.extend(page_weibos)
        print(f"页面 {pages[i]} 获取到 {len(page_weibos)} 条数据")

    print(f"批量爬取完成，总共获取到 {len(all_weibos)} 条数据")
    return all_weibos

def process_weibo_data(mblog):
    """
    处理微博数据
    :param mblog: 微博数据字典
    :return: 处理后的数据字典
    """
    try:
        if not mblog:
            return None
            
        weibo_id = mblog.get('id', 'N/A')
        bid = mblog.get('bid', 'N/A')
        user = mblog.get('user', {})
        
        # 获取用户性别信息
        gender = user.get('gender', '')
        if gender == 'm':
            gender = '男'
        elif gender == 'f':
            gender = '女'
        else:
            gender = '未知'
            
        return {
            '微博id': weibo_id,
            '微博bid': bid,
            '微博作者': user.get('screen_name', '未知作者'),
            '发布时间': mblog.get('created_at', 'N/A'),
            '微博内容': re.sub(r'<[^>]+>', '', mblog.get('text', '无内容')),
            '转发数': mblog.get('reposts_count', 0),
            '评论数': mblog.get('comments_count', 0),
            '点赞数': mblog.get('attitudes_count', 0),
            '国家': mblog.get('status_country', 'N/A'),
            '省份': mblog.get('status_province', 'N/A'),
            '城市': mblog.get('status_city', 'N/A'),
            '用户简介': user.get('description', ''),
            '用户关注数': user.get('follow_count', 0),
            '粉丝数': user.get('followers_count', 0),
            '性别': gender,
            '主页': f"https://weibo.com/u/{user.get('id', '')}",
            'url': f"https://m.weibo.cn/detail/{bid}",
            'uni_id': bid
        }
    except Exception as e:
        print(f"处理微博数据时出错: {str(e)}")
        return None

@monitor_performance('get_weibo_list')
def get_weibo_list(keyword, max_page):
    """
    获取微博列表（优化版本，支持并发爬取）
    :param keyword: 关键词
    :param max_page: 最大页数
    :return: DataFrame
    """
    try:
        print(f"开始爬取微博数据: 关键词={keyword}, 最大页数={max_page}")

        # 限制最大页数，避免过度请求
        max_page = min(max_page, 50)

        # 决定是否使用并发爬取
        use_concurrent = max_page > 3 and PERFORMANCE_CONFIG.get('enable_concurrent_crawling', True)

        if use_concurrent:
            # 并发爬取
            pages = list(range(1, max_page + 1))
            data_list = crawl_weibo_pages_batch(keyword, pages)
        else:
            # 串行爬取（小页数时）
            data_list = []
            for page in range(1, max_page + 1):
                try:
                    items = crawl_weibo_page(keyword, page)
                    if items:
                        data_list.extend(items)

                    # 添加延迟，避免请求过快
                    if page < max_page:
                        time.sleep(random.uniform(0.5, 1.5))

                except Exception as e:
                    print(f"爬取第{page}页时出错: {str(e)}")
                    continue

        # 数据处理和清理
        if data_list:
            print(f"原始数据数量: {len(data_list)}")

            # 去重处理
            unique_data = []
            seen_ids = set()
            for item in data_list:
                item_id = item.get('微博id') or item.get('uni_id')
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_data.append(item)

            print(f"去重后数据数量: {len(unique_data)}")

            # 创建DataFrame
            df = pd.DataFrame(unique_data)

            # 确保所需列存在
            required_columns = ['微博id', '微博bid', '微博作者', '微博内容', '发布时间', '转发数', '评论数', '点赞数', 'url']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 'N/A'

            # 批量处理时间格式
            df['发布时间'] = df['发布时间'].apply(
                lambda x: trans_time(x) if pd.notna(x) and x != 'N/A' else 'N/A'
            )

            # 批量处理数值列
            numeric_columns = ['转发数', '评论数', '点赞数']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 保存到文件
            temp_file = get_temp_file_path('weibo', keyword)
            persistent_file = get_persistent_file_path('weibo', keyword)

            # 使用优化的CSV写入
            from utils.csv_optimizer import csv_optimizer
            csv_optimizer.write_csv_optimized(df, temp_file)
            update_persistent_file(temp_file, 'weibo', keyword)

            print(f"数据已保存到: {temp_file}")
            print(f"爬虫统计: {spider_optimizer.get_stats()}")

            # 内存清理
            del data_list, unique_data
            gc.collect()

            return df
        else:
            print("未获取到任何数据")
            # 返回空DataFrame
            return pd.DataFrame(columns=['微博id', '微博bid', '微博作者', '微博内容', '发布时间', '转发数', '评论数', '点赞数', 'url'])

    except Exception as e:
        print(f"获取微博列表时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        # 返回空DataFrame
        return pd.DataFrame(columns=['微博id', '微博bid', '微博作者', '微博内容', '发布时间', '转发数', '评论数', '点赞数', 'url'])
