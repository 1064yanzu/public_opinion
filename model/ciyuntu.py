import jieba
import wordcloud
import imageio
import numpy as np
from PIL import Image
import csv
import os
import pandas as pd

stopwords = set()
with open("stopwords.txt", 'r', encoding='utf-8') as f:
    for line in f.readlines():
        stopwords.add(line.strip())
def remove_stopwords(text):
    # 分词
    words = str(jieba.lcut(text))
    # 去除停用词
    filtered_text = [word for word in words if word.casefold() not in stopwords]
    return ' '.join(filtered_text)
def read_weibo_content(csv_path):

    df = pd.read_csv(csv_path)
    weibo_content_list = []
    # 检查是否存在‘微博内容’这一列
    if '微博内容' in df.columns:
        # 提取‘微博内容’列的内容
        weibo_content_list = df['微博内容'].tolist()

    elif '视频描述' in df.columns:
        weibo_content_list = df['视频描述'].tolist()
    return weibo_content_list

def get_wordcloud_csv(csv_path):
    # 获取当前脚本的绝对路径
    script_dir = os.path.abspath(__file__)

    # 计算项目根目录的绝对路径
    project_root = os.path.dirname(os.path.dirname(script_dir))

    # 拼接 CSV 文件的完整路径
    csv_path = os.path.join(project_root, csv_path)
    print(csv_path)
    global weibo_content_list
    weibo_content_list = read_weibo_content(csv_path)
    filtered_contents = []
    for row in weibo_content_list:
        cleaned_text = remove_stopwords(str(row))
        filtered_contents.append(cleaned_text)
    combined_text = ' '.join(filtered_contents)
    img = Image.open("xuexi.jpg")
    img = img.convert('RGBA')
    r, g, b, a = img.split()
    img = Image.merge('RGB', (r, g, b))
    img = img.resize((1000, 1000), Image.LANCZOS)
    # img = img.resize((1000, 1000), Image.ANTIALIAS)
    background_image = np.array(img)
    # 构建并配置词云对象w，注意要加scale参数，提高清晰度
    mk = background_image
    # if int(input("您是否需要调整词云图的参数，需要请输入1")) !=1 :
    w = wordcloud.WordCloud(width=1500,
                        height=3000,
                        max_words=400,
       #                 max_font_size = 130,
                        background_color='white',
                        font_path="三极泼墨体.ttf",
                        mask=mk,
                        scale=1,
                        collocations= False,
    #                     contour_width=0.05,
                        stopwords=stopwords)

    print('正在分词')

    # 对mask中每个像素的颜色进行记录
    mk_colors = np.array(mk)

    print('正在记录颜色')

    # 生成词云图
    w.generate(combined_text or '')

    print('正在生成词云图')

    # 将词云图中与mask中每个像素点颜色一致的词语的颜色也设置为相应的颜色
    mask_colors = wordcloud.ImageColorGenerator(mk_colors)
    w.recolor(color_func=mask_colors)

    print('正在调整颜色')

    f.close()

    # 输出词云图
    w.to_file('static\\assets\\images\wordcloud.png')

if __name__ == '__main__':
    get_wordcloud_csv('软件.csv')
