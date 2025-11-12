import jieba
import wordcloud
import imageio
import numpy as np
from PIL import Image
import csv
import os
import pandas as pd
import re
import gc
from utils.cache_manager import cached, memory_cleanup
from utils.csv_optimizer import csv_optimizer
from config.settings import PERFORMANCE_CONFIG

# 加载停用词
stopwords = set()
with open("stopwords.txt", 'r', encoding='utf-8') as f:
    for line in f.readlines():
        stopwords.add(line.strip())

def clean_text(text):
    """清理文本，只移除无用信息，保留所有中文内容"""
    try:
        # 转换为字符串
        text = str(text)
        
        # 移除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 移除@用户
        text = re.sub(r'@[\w\-]+', '', text)
        
        # 移除话题标签
        text = re.sub(r'#.*?#', '', text)
        
        # 移除表情符号
        text = re.sub(r'\[.*?\]', '', text)
        
        return text
    except:
        return ""

def remove_stopwords(text):
    """分词并移除停用词"""
    # 清理文本
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return ""
    
    # 使用jieba进行分词
    words = jieba.lcut(cleaned_text)
    
    # 过滤停用词和空字符
    filtered_words = []
    for word in words:
        word = word.strip()
        if not word or word in stopwords or word.isspace():
            continue
        
        # 检查词语类型
        if len(word) >= 2 and re.search(r'[\u4e00-\u9fff]', word):  # 中文词至少2个字
            filtered_words.append(word)
        elif re.match(r'^[a-zA-Z]{3,}$', word):  # 英文词至少3个字母
            filtered_words.append(word.lower())
    
    return ' '.join(filtered_words)

@cached(ttl=1800, key_prefix="weibo_content")
def read_weibo_content(csv_path):
    """读取微博内容（优化版本，带缓存）"""
    try:
        # 使用优化的CSV读取
        df = csv_optimizer.read_csv_optimized(csv_path)
        if df.empty:
            print("错误: CSV文件为空或读取失败")
            return []

        print(f"成功读取CSV文件，数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")

        # 尝试不同的列名
        content_columns = ['微博内容', '视频描述', '内容', 'content', 'text']
        content_column = None

        for col in content_columns:
            if col in df.columns:
                content_column = col
                break

        if content_column is None:
            print("错误: 找不到内容列")
            return []

        print(f"使用列: {content_column}")

        # 批量处理内容，移除空值和重复值
        content_series = df[content_column].dropna().drop_duplicates()
        content_series = content_series[content_series.astype(str).str.strip() != '']
        weibo_content_list = content_series.astype(str).str.strip().tolist()

        print(f"成功读取 {len(weibo_content_list)} 条有效内容")

        # 内存清理
        del df, content_series
        gc.collect()

        return weibo_content_list

    except Exception as e:
        print(f"读取CSV文件时出错: {str(e)}")
        return []

def get_wordcloud_csv(csv_path):
    """
    生成词云图（优化版本）
    :param csv_path: CSV文件路径
    """
    try:
        # 获取当前脚本的绝对路径
        script_dir = os.path.abspath(__file__)

        # 计算项目根目录的绝对路径
        project_root = os.path.dirname(os.path.dirname(script_dir))

        # 拼接 CSV 文件的完整路径
        csv_path = os.path.join(project_root, csv_path)
        print("正在处理文件:", csv_path)

        # 读取微博内容
        weibo_content_list = read_weibo_content(csv_path)
        if not weibo_content_list:
            print("警告: 没有找到有效的微博内容")
            return

        # 批量文本预处理
        print("正在进行文本预处理...")
        batch_size = PERFORMANCE_CONFIG.get('batch_size', 100)
        filtered_contents = []

        for i in range(0, len(weibo_content_list), batch_size):
            batch = weibo_content_list[i:i + batch_size]
            batch_results = []

            for content in batch:
                if content and isinstance(content, str):
                    # 应用文本清理和分词
                    processed_text = remove_stopwords(content)
                    if processed_text.strip():
                        batch_results.append(processed_text)

            filtered_contents.extend(batch_results)

            # 内存管理
            if i % (batch_size * 5) == 0 and i > 0:
                print(f"已处理 {i}/{len(weibo_content_list)} 条内容")
                gc.collect()

        if not filtered_contents:
            print("错误: 处理后没有有效的文本内容")
            return

        # 合并文本
        combined_text = ' '.join(filtered_contents)
        print(f"处理后的文本长度: {len(combined_text)} 字符")
        print("处理后的部分文本示例:", combined_text[:200])

        # 内存清理
        del weibo_content_list, filtered_contents
        gc.collect()
    
        try:
            # 读取背景图片
            img = Image.open("xuexi.jpg")
            img = img.convert('RGBA')
            r, g, b, a = img.split()
            img = Image.merge('RGB', (r, g, b))
            img = img.resize((1000, 1000), Image.LANCZOS)
            background_image = np.array(img)

            print("正在生成词云...")
            # 配置词云参数
            w = wordcloud.WordCloud(
                width=1500,
                height=3000,
                max_words=400,
                background_color='white',
                font_path="三极泼墨体.ttf",
                mask=background_image,
                scale=1,
                collocations=False,
                min_font_size=10,
                max_font_size=150,
                random_state=42,
                stopwords=stopwords,
                prefer_horizontal=0.9,  # 水平文字的比例
                repeat=True,  # 允许词语重复出现
                font_step=1,  # 字体大小的步进
                relative_scaling=0.6  # 词频和字体大小的关联程度
            )

            # 生成词云
            w.generate_from_text(combined_text)

            # 根据背景图着色
            mask_colors = wordcloud.ImageColorGenerator(background_image)
            w.recolor(color_func=mask_colors)

            # 保存词云图
            output_path = os.path.join(project_root, 'static/assets/images', 'wordcloud.png')
            os.makedirs(os.path.dirname(output_path), exist_ok=True)  # 确保目录存在
            w.to_file(output_path)
            print(f"词云图已保存至: {output_path}")

            # 内存清理
            del img, background_image, w, mask_colors, combined_text
            gc.collect()

        except Exception as e:
            print(f"生成词云图时发生错误: {str(e)}")

    except Exception as e:
        print(f"词云生成过程出错: {str(e)}")
        memory_cleanup()  # 出错时清理内存

if __name__ == '__main__':
    get_wordcloud_csv('temp_data/weibo_山东大学.csv')