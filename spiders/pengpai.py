import csv
import requests
import os
from urllib.parse import urlparse
from datetime import datetime

# 获取当前日期并格式化
current_date = datetime.now().strftime('%Y%m%d')


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42",
    "accept": "application/json, text/plain, */*",
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'client-type': '2'
}

def download_image(url, path):
    """下载图片并保存到指定路径"""
    try:
        response = requests.get(url, stream=True, headers=headers)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return True
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
    return False

def spider(url):
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    return response.json()

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
            filename = f'{title}.jpg'  # 清理标题作为文件名
            save_path = os.path.join(images_dir, filename)
            read_link = f'/content/{filename}'

            # 下载并保存图片
            if download_image(cover_image, save_path):
                writer.writerow({
                    '发文者': writer_name,
                    '标题': title,
                    '封面链接': save_path,
                    '链接': link,
                    'down_link': read_link
                })
                daily_hotspots.append({
                    'title': title,
                    'cover_image': cover_image,  # 保存相对路径
                    'source': writer_name,
                    'link': link,
                    'read_link': read_link
                })

    return daily_hotspots

if __name__ == '__main__':
    hotspots = get_pengpai_list()
    print(hotspots)