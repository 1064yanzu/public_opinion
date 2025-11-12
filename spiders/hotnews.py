import requests
import json

url1 = 'https://www.weibo.com/ajax/side/hotSearch'
url2 = 'https://www.douyin.com/aweme/v1/web/hot/search/list'
def get_hot_dy():
    headers = {
            'scheme':'https',
            'accept':'application/json, text/plain, */*',
            'priority':
            'u=1, i',
            'referer':
            'https://www.douyin.com/hot',
            'sec-fetch-dest':'empty',
            'sec-fetch-mode':'cors',
            'sec-fetch-site':'same-origin',
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url2, headers=headers)
        response.raise_for_status()
        datas = response.json()['data']['word_list']
        news = []
        for data in datas:
            word = data['word']
            sentence_id = data['sentence_id']
            video_url = f'https://www.douyin.com/hot?modal_id={sentence_id}'
            news.append({ word: video_url})
        return news
    except:
        print('请求失败')


if __name__ == '__main__':
    news = get_hot_dy()
    print(news)








#     # 提取政府相关话题和实时热门话题
#     govtitles = [topic['word'] for topic in data['data']['hotgovs']]
#     titles = [topic['word'] for topic in data['data']['realtime']]
#
#     # 打印置顶评论和实时热门话题
#     for idx, title in enumerate(govtitles, start=1):
#         print(f'置顶评论 {idx}. {title}')
#     for idx, title in enumerate(titles, start=1):
#         print(f'{idx}. {title}')
# except requests.exceptions.RequestException as e:  # 例如网络错误等
#     print(f'请求失败: {e}')
# except json.JSONDecodeError:
#     print('无法解析JSON响应。')
