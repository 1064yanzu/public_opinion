import os.path
import re
from jsonpath import jsonpath
import requests
import pandas as pd
from datetime import datetime
import os
import time
import random

from utils.common import get_persistent_file_path, get_temp_file_path, update_persistent_file
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

def crawl_weibo_page(keyword, page):
    """
    爬取单页微博数据
    :param keyword: 关键词
    :param page: 页码
    :return: 数据列表
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br"
        }
        
        url = 'https://m.weibo.cn/api/container/getIndex'
        params = {
            "containerid": f"100103type=1&q={keyword}",
            "page_type": "searchall",
            "page": page
        }
        
        r = requests.get(url, headers=headers, params=params)
        cards = r.json()["data"]["cards"]
        
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
        
        return weibos
    except Exception as e:
        print(f"爬取微博页面时出错: {str(e)}")
        return []

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

def get_weibo_list(keyword, max_page):
    """
    获取微博列表
    :param keyword: 关键词
    :param max_page: 最大页数
    :return: DataFrame
    """
    try:
        # 初始化数据列表
        data_list = []
        
        # 爬取数据
        for page in range(1, max_page + 1):
            try:
                items = crawl_weibo_page(keyword, page)
                if items:
                    data_list.extend(items)
                time.sleep(random.uniform(1, 3))  # 随机延迟
            except Exception as e:
                print(f"爬取第{page}页时出错: {str(e)}")
                continue
        
        # 创建DataFrame
        if data_list:
            df = pd.DataFrame(data_list)
            
            # 确保所需列存在
            required_columns = ['微博id', '微博bid', '微博作者', '微博内容', '发布时间', '转发数', '评论数', '点赞数', 'url']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 'N/A'
            
            # 处理时间格式
            df['发布时间'] = df['发布时间'].apply(lambda x: trans_time(x) if pd.notna(x) and x != 'N/A' else 'N/A')
            
            # 处理数值列
            numeric_columns = ['转发数', '评论数', '点赞数']
            for col in numeric_columns:
                df[col] = df[col].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
            
            return df
        else:
            # 返回空DataFrame
            return pd.DataFrame(columns=['微博id', '微博bid', '微博作者', '微博内容', '发布时间', '转发数', '评论数', '点赞数', 'url'])
            
    except Exception as e:
        print(f"获取微博列表时出错: {str(e)}")
        # 返回空DataFrame
        return pd.DataFrame(columns=['微博id', '微博bid', '微博作者', '微博内容', '发布时间', '转发数', '评论数', '点赞数', 'url'])
