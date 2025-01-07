import os.path
import re
from jsonpath import jsonpath
import requests
import pandas as pd
from datetime import datetime
import pymysql
import os

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

def get_weibo_list(v_keyword, v_max_page):
    # 初始化一个空DataFrame以收集所有页面的数据
    global result
    all_data = pd.DataFrame()
    for page in range(1, v_max_page + 1):
        print('===开始爬取第{}页微博==='.format(page))
        # 请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br"
        }
        # 请求地址
        url = 'https://m.weibo.cn/api/container/getIndex'
        # 请求参数
        params = {
            "containerid": "100103type=1&q={}".format(v_keyword),
            "page_type": "searchall",
            "page": page
        }
        # 发送请求
        r = requests.get(url, headers=headers, params=params)
        # 解析json数据
        cards = r.json()["data"]["cards"]

        # 初始化一个空列表来存储每条微博的信息
        weibos = []

        for card in cards:
            card_type = card.get('card_type')

            if card_type == 9:
                mblog = card.get('mblog', {})
                weibo_id = mblog.get('bid', 'N/A')
                # 提取信息并填充缺失值
                weibo_info = {
                    '微博id': mblog.get('user', {}).get('id', 'N/A'),
                    'uni_id': weibo_id,
                    '微博作者': mblog.get('user', {}).get('screen_name', 'N/A'),
                    '发布时间': mblog.get('created_at', 'N/A'),  # 直接使用原始值
                    '微博内容': re.sub(r'<[^>]+>', '', mblog.get('text', 'N/A')),
                    '转发数': mblog.get('reposts_count', 'N/A'),
                    '评论数': mblog.get('comments_count', 'N/A'),
                    '点赞数': mblog.get('attitudes_count', 'N/A'),
                    '国家': mblog.get('status_country', 'N/A'),
                    '省份': mblog.get('status_province', 'N/A'),
                    '城市': mblog.get('status_city', 'N/A'),
                    '用户简介': mblog.get('user', {}).get('description', 'N/A'),
                    '用户关注数': mblog.get('user', {}).get('follow_count', 'N/A'),
                    '粉丝数': mblog.get('user', {}).get('followers_count_str', 'N/A'),
                    '性别': mblog.get('user', {}).get('gender', 'N/A'),
                    '主页': mblog.get('user', {}).get('profile_url', 'N/A'),
                    'url': f"https://m.weibo.cn/detail/{weibo_id}"
                }

                # 将每条微博的信息添加到列表中
                weibos.append(weibo_info)
            elif card_type == 11:
                # 当 card_type 为 11 时，从 card_group 的第一个字典中提取信息
                card_group = card.get('card_group', [])
                if card_group:
                    first_item = card_group[0]
                    mblog = first_item.get('mblog', {})
                    weibo_id = mblog.get('bid', 'N/A')
                    # 提取信息并填充缺失值
                    weibo_info = {
                        '微博id': mblog.get('user', {}).get('id', 'N/A'),
                        '微博bid': weibo_id,
                        '微博作者': mblog.get('user', {}).get('screen_name', 'N/A'),
                        '发布时间': mblog.get('created_at', 'N/A'),  # 直接使用原始值
                        '微博内容': re.sub(r'<[^>]+>', '', mblog.get('text', 'N/A')),
                        '转发数': mblog.get('reposts_count', 'N/A'),
                        '评论数': mblog.get('comments_count', 'N/A'),
                        '点赞数': mblog.get('attitudes_count', 'N/A'),
                        '国家': mblog.get('status_country', 'N/A'),
                        '省份': mblog.get('status_province', 'N/A'),
                        '城市': mblog.get('status_city', 'N/A'),
                        '用户简介': mblog.get('user', {}).get('description', 'N/A'),
                        '用户关注数': mblog.get('user', {}).get('follow_count', 'N/A'),
                        '粉丝数': mblog.get('user', {}).get('followers_count_str', 'N/A'),
                        '性别': mblog.get('user', {}).get('gender', 'N/A'),
                        '主页': mblog.get('user', {}).get('profile_url', 'N/A'),
                        'url': f"https://m.weibo.cn/detail/{weibo_id}"
                    }

                    # 将每条微博的信息添加到列表中
                    weibos.append(weibo_info)

        # 创建 DataFrame
        df = pd.DataFrame(weibos)

        # 在 DataFrame 中转换时间字段
        df['发布时间'] = df['发布时间'].apply(lambda x: trans_time(x) if x != 'N/A' else 'N/A')

        # 过滤掉所有内容都是 'N/A' 的行
        df = df.loc[~(df == 'N/A').all(axis=1)]

        # 将当前页面的数据追加到总数据集
        all_data = pd.concat([all_data, df], ignore_index=True)

        # 使用新的文件路径函数
        persistent_file = get_persistent_file_path('weibo', v_keyword)
        temp_file = get_temp_file_path('weibo')
        
        # 保存数据到临时文件
        all_data.to_csv(temp_file, index=False, encoding='utf-8-sig')
        
        # 更新持久文件
        update_persistent_file(persistent_file, temp_file)

        # 将 DataFrame 转换为列表包裹的字典形式
        result = all_data.to_dict(orient='records')

    return result
