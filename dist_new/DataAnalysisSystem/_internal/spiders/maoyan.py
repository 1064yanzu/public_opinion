import requests
from urllib.parse import quote
import pandas as pd
import time
import random

def get_type(keyword):
    keyword2 = quote(keyword)
    url_one = f'https://m.douban.com/rexxar/api/v2/search?q={keyword2}&type=&loc_id=&start=0&count=10&sort=relevance'
    params = {
        'q': keyword,
        'type':'',
        'loc_id':'',
        'start': '0',
        'count': '10',
        'sort': 'relevance'
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
        'Accept': 'application/json, text/plain, */*',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        # 'scheme':'https',
        'priority':'u=1, i',
        # 'cache - control':'max - age = 0',
        'origin': 'https://www.douban.com',
        'referer':f'https://www.douban.com/search?q={keyword2}',
        'Sec-Ch-Ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': "Windows",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'cookie':'bid=14l63NpxALY; ll="118227"; douban-fav-remind=1; _ga=GA1.1.1827390446.1725885933; _ga_RXNMP372GL=GS1.1.1725886134.1.1.1725886145.49.0.0; viewed="1941049_1072313"; __utma=30149280.1827390446.1725885933.1728701325.1728733761.3; __utmc=30149280; __utmz=30149280.1728733761.3.3.utmcsr=cn.bing.com|utmccn=(referral)|utmcmd=referral|utmcct=/; ap_v=0,6.0; __utmt=1; __utmb=30149280.10.10.1728733761'
    }
    response = requests.get(url_one, headers=headers)
    response.raise_for_status()
    print(response)
    datas = response.json()['subjects']['items']
    for data in datas:
        print(data)
        is_movie = data['type_name']
        if is_movie == "电影":
            type_name = data['target']['card_subtitle']
            print(type_name)
            return type_name
        else:
            pass






# def main(file_path):
#
#     df = pd.read_excel(file_path)
#
#     # 新增一列“类型”
#     df['类型'] = None
#
#     # 遍历每一行，获取电影类型
#     for index, row in df.iterrows():
#         movie_name = row['电影']
#         if pd.notna(movie_name):  # 检查是否为空
#             try:
#                 movie_type = get_type(movie_name)
#             except Exception as e:
#                 movie_type = 'null'
#                 print(f"获取电影类型时发生错误：{e}")
#             sleep = random.randint(15,20)
#             time.sleep(sleep)
#             df.at[index, '类型'] = movie_type
#
#     # 保存回Excel文件
#     try:
#         df.to_excel(file_path, index=False
#                     )
#     except:
#         print(df)
#     print("数据已保存到Excel文件")
def main(file_path, reference_files):
    # 加载参考文件
    reference_data = pd.DataFrame()
    for ref_file in reference_files:
        try:
                ref_df = pd.read_excel(ref_file, usecols=['电影', '类型'])
                reference_data = pd.concat([reference_data, ref_df], ignore_index=True)
        except:
            print(ref_file)
            pass

    # 去重
    reference_data.drop_duplicates(subset=['电影'], keep='first', inplace=True)

    # 主文件加载
    df = pd.read_excel(file_path)

    # 新增一列“类型”
    df['类型'] = None

    # 创建一个字典用于快速查找
    ref_dict = dict(zip(reference_data['电影'], reference_data['类型']))

    # 遍历每一行，获取电影类型
    for index, row in df.iterrows():
        movie_name = row['电影']
        if pd.notna(movie_name):  # 检查是否为空
            if movie_name in ref_dict:  # 如果电影名存在于参考文件中
                df.at[index, '类型'] = ref_dict[movie_name]
                print(f'{movie_name}有参考')
            else:
                try:
                    print(f'{movie_name}无可参考')
                    movie_type = get_type(movie_name)
                    sleep = random.randint(15, 20)
                    time.sleep(sleep)
                except Exception as e:
                    movie_type = 'null'
                    print(f"获取电影类型时发生错误：{e}")
                df.at[index, '类型'] = movie_type

    # 保存回Excel文件
    try:
        df.to_excel(file_path, index=False)
    except Exception as e:
        print(f"保存文件时发生错误：{e}")
        print(df)
    print("数据已保存到Excel文件")


if __name__ == '__main__':
    # 读取Excel文件
    file_path = "D:\\桌面\\数据新闻\\结果\\2016暑期.xlsx"  # 替换为你的Excel文件路径
    reference_files = ["D:\\桌面\\数据新闻\\结果\\merged.xlsx"]  # 添加所有参考文件路径
    main(file_path, reference_files)




# if __name__ == '__main__':
#     # 读取Excel文件
#     file_path = "D:\\桌面\\数据新闻\\结果\\2013端午.xlsx"  # 替换为你的Excel文件路径
#     main(file_path)

