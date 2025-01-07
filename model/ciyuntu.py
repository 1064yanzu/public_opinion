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
    
    # 检查可能的内容列名
    content_columns = ['内容', '微博内容', '视频描述']
    for col in content_columns:
        if col in df.columns:
            content_list = df[col].dropna().tolist()
            if content_list:  # 如果找到非空内容
                weibo_content_list.extend(content_list)
                break
    
    # 如果没有找到任何内容，打印警告
    if not weibo_content_list:
        print(f"警告：在CSV文件中未找到有效的内容列。可用列名：{df.columns.tolist()}")
        
    return weibo_content_list

def get_wordcloud_csv(csv_path):
    # 获取当前脚本的绝对路径
    script_dir = os.path.abspath(__file__)

    # 计算项目根目录的绝对路径
    project_root = os.path.dirname(os.path.dirname(script_dir))

    # 拼接 CSV 文件的完整路径
    csv_path = os.path.join(project_root, csv_path)
    print(f"正在处理文件：{csv_path}")
    
    try:
        # 读取内容
        weibo_content_list = read_weibo_content(csv_path)
        if not weibo_content_list:
            raise ValueError("没有找到有效的内容数据")
            
        # 过滤和清理内容
        filtered_contents = []
        for row in weibo_content_list:
            if pd.notna(row) and str(row).strip():  # 确保内容非空且非空白
                cleaned_text = remove_stopwords(str(row))
                if cleaned_text.strip():  # 确保清理后的文本非空
                    filtered_contents.append(cleaned_text)
        
        if not filtered_contents:
            raise ValueError("清理后没有有效的内容数据")
            
        # 合并文本
        combined_text = ' '.join(filtered_contents)
        
        # 加载背景图片
        img = Image.open("xuexi.jpg")
        img = img.convert('RGBA')
        r, g, b, a = img.split()
        img = Image.merge('RGB', (r, g, b))
        img = img.resize((1000, 1000), Image.LANCZOS)
        background_image = np.array(img)
        
        # 构建词云对象
        w = wordcloud.WordCloud(
            width=1500,
            height=3000,
            max_words=400,
            background_color='white',
            font_path="三极泼墨体.ttf",
            mask=background_image,
            scale=1,
            collocations=False,
            stopwords=stopwords
        )
        
        print('正在生成词云图...')
        w.generate(combined_text)
        
        print('正在调整颜色...')
        mask_colors = wordcloud.ImageColorGenerator(background_image)
        w.recolor(color_func=mask_colors)
        
        # 保存词云图
        output_path = os.path.join('static', 'assets', 'images', 'wordcloud.png')
        w.to_file(output_path)
        print(f'词云图已保存到：{output_path}')
        
    except Exception as e:
        print(f"生成词云图时出错：{str(e)}")
        raise

if __name__ == '__main__':
    get_wordcloud_csv('软件.csv')