import csv
import requests
import os
from datetime import datetime

# 获取当前日期并格式化
current_date = datetime.now().strftime('%Y%m%d')


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42",
    "accept": "application/json, text/plain, */*",
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'client-type': '2'
}

# 移除图片下载功能，专注于数据获取

def spider(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查HTTP错误
        response.encoding = 'utf-8'
        return response.json()
    except requests.exceptions.Timeout:
        print(f"请求超时: {url}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        raise
    except Exception as e:
        print(f"解析JSON失败: {e}")
        raise

def get_pengpai_list(save_folder='content'):
    url = 'https://cache.thepaper.cn/contentapi/contVisit/hotNews'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    static_dir = os.path.join(parent_dir, 'static')
    images_dir = os.path.join(static_dir, save_folder)

    # 确保content子目录存在
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    r_data = spider(url)
    datas = r_data['data']

    csv_file_name = f'{current_date}_pengpai.csv'
    csv_file_path = os.path.join(images_dir, csv_file_name)

    with open(csv_file_path, 'w', encoding='utf-8', newline='') as f:
        heads = ['发文者', '标题', '封面链接', '链接', 'down_link']
        writer = csv.DictWriter(f, fieldnames=heads)
        writer.writeheader()
        daily_hotspots = []

        for data in datas:
            contid = data['contId']
            title = data['name']
            writer_name = data['nodeInfo']['name']
            cover_image = data['voiceInfo']['imgSrc']
            link = f'https://m.thepaper.cn/newsDetail_forward_{contid}'
            # 直接保存数据，不下载图片
            writer.writerow({
                '发文者': writer_name,
                '标题': title,
                '封面链接': cover_image,  # 保存原始图片链接
                '链接': link,
                'down_link': link  # 使用原始链接
            })

            daily_hotspots.append({
                'title': title,
                'cover_image': cover_image,  # 使用原始图片链接
                'source': writer_name,
                'link': link,
                'read_link': link
            })

    return daily_hotspots

if __name__ == '__main__':
    hotspots = get_pengpai_list()
    print(hotspots)