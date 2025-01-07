import os
import traceback
from snownlp import SnowNLP
import pandas as pd
from datetime import datetime
import ast
from utils.common import update_persistent_file,get_persistent_file_path,get_temp_file_path
from spiders.articles_spider import get_weibo_list
from spiders.douyin import get_douyin_list

ready_path = get_persistent_file_path('all','any')
def target_file():
    target_file = 'target.csv'
    # comments = getAllCommentsData()
    # 读取 CSV 文件
    df = pd.read_csv('E:\\python\\flaskProject\\spiders\\王冰冰.csv')
    print(df.head())

    # 初始化计数器
    good, bad, middle = 0, 0, 0
    rate_data = []

    # 假设您要分析的列名为 'comment'
    for index, row in df().iterrows():
        value = SnowNLP(row['text']).sentiments
        if value > 0.5:
            good += 1
            rate_data.append((row['text'], '正面'))
        elif value < 0.5:
            bad += 1
            rate_data.append((row['text'], '负面'))
        else:
            middle += 1
            rate_data.append((row['text'], '中性'))
    # 打印结果
    print(f"正面评论数: {good}")
    print(f"负面评论数: {bad}")
    print(f"中性评论数: {middle}")

def get_info2(csv_path):
    try:
        df = pd.read_csv(csv_path)
        print(f"读取的 CSV 文件: {csv_path}")
        print(f"DataFrame 的列: {df.columns.tolist()}")
        
        if df.empty:
            print("警告：DataFrame 为空")
            return [], 0, 0, 0, {}
        
        infos2_data = df.to_dict(orient='records')
        
        # 使用更健壮的方法获取数值
        share_num = int(df['分享数'].sum()) if '分享数' in df.columns else 0
        comment_num = int(df['评论数'].sum()) if '评论数' in df.columns else 0
        like_num = int(df['点赞数'].sum()) if '点赞数' in df.columns else 0
        
        sentiment_counts = df['情感倾向'].value_counts().to_dict() if '情感倾向' in df.columns else {}
        
        print(f"返回的数据类型: infos2_data: {type(infos2_data)}, share_num: {type(share_num)}, comment_num: {type(comment_num)}, like_num: {type(like_num)}, sentiment_counts: {type(sentiment_counts)}")
        return infos2_data, share_num, comment_num, like_num, sentiment_counts
    except Exception as e:
        print(f"get_info2 函数出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return [], 0, 0, 0, {}
    # # 读取CSV文件
    # df = pd.read_csv(csv_path)

    # # 将DataFrame转换为字典列表
    # infos2_data = df.to_dict(orient='records')
    # try:
    #     # 对各列进行求和
    #     summary = df[['分享数', '评论数', '点赞数']].sum(numeric_only=True)  # numeric_only=True确保只对数值型列求和

    #     # 确保即使在极端情况下（比如某列在CSV中无数据）也能安全访问
    #     share_num = summary.get('分享数', 0)
    #     comment_num = summary.get('评论数', 0)
    #     like_num = summary.get('点赞数', 0)

    #     # 计算各个情感态度的数量
    #     sentiment_counts = df['情感倾向'].value_counts().to_dict()
    # except:
    #     # 对各列进行求和
    #     summary = df[['转发数', '评论数', '点赞数']].sum(numeric_only=True)  # numeric_only=True确保只对数值型列求和

    #     # 确保即使在极端情况下（比如某列在CSV中无数据）也能安全访问
    #     share_num = summary.get('转发数', 0)
    #     comment_num = summary.get('评论数', 0)
    #     like_num = summary.get('点赞数', 0)
    #     sentiment_counts = {
    #         '正面': 0,
    #         '负面': 0,
    #         '中性': 0
    #     }

    # return infos2_data, share_num, comment_num, like_num, sentiment_counts

def get_info3(csv_path):
    # 读取CSV文件
    df = pd.read_csv(csv_path)
    # 将DataFrame转换为字典列表
    infos2_data = df.to_dict(orient='records')
    return infos2_data

def get_ip(csv_path =ready_path):
    # 读取CSV文件
    try:
        df = pd.read_csv(csv_path)
        # 对省份进行计数
        province_counts = df['省份'].value_counts().to_dict()
        # 构建返回的数据结构
        ips = [
            {
                "province": province,
                "value": value
            }
            for province, value in province_counts.items()
        ]

    except:
        ips = []

    return ips

    # 确保即使在极端情况下（比如某列在CSV中无数据）也能安全访问
    share_num = summary.get('转发数', 0)
    comment_num = summary.get('评论数', 0)
    like_num = summary.get('点赞数', 0)

    return infos2_data, share_num, comment_num, like_num

def analyze_sentiment(text):
    """
    分析文本情感倾向
    :param text: 待分析的文本
    :return: 情感标签 (positive/negative/neutral)
    """
    try:
        if pd.isna(text) or not isinstance(text, str):
            return 'neutral'
            
        sentiment_score = SnowNLP(str(text)).sentiments
        
        if sentiment_score > 0.7:
            return 'positive'
        elif sentiment_score < 0.3:
            return 'negative'
        else:
            return 'neutral'
            
    except Exception as e:
        print(f"情感分析出错: {str(e)}, 文本: {text}")
        return 'neutral'

def convert_sentiment_to_text(score):
    """
    将情感分数转换为文字描述
    :param score: 情感分数
    :return: 情感文字描述
    """
    try:
        if isinstance(score, str):
            if score == 'positive':
                return '正面'
            elif score == 'negative':
                return '负面'
            else:
                return '中性'
                
        score = float(score)
        if score > 0.7:
            return '正面'
        elif score < 0.3:
            return '负面'
        else:
            return '中性'
    except (ValueError, TypeError):
        return '中性'

def nlp_weibo(csv_path):
    """
    处理微博数据的情感分析
    :param csv_path: CSV文件路径
    """
    print(f"开始处理微博数据: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")

        def safe_sentiment(content):
            if pd.isna(content) or not isinstance(content, str):
                return 0.5  # 默认中性情感
            try:
                return SnowNLP(str(content)).sentiments
            except Exception as e:
                print(f"情感分析错误: {str(e)}, 内容: {content}")
                return 0.5  # 出错时返回中性情感

        # 进行情感分析
        df['情感倾向'] = df['微博内容'].apply(safe_sentiment)
        print("情感分析完成")
        print(f"情感分析结果的前几行:\n{df['情感倾向'].head()}")
        
        # 保存结果
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        df.to_csv(ready_path, index=False, encoding='utf-8-sig')
        print(f"处理后的数据已保存到: {csv_path}")
        
    except Exception as e:
        print(f"处理微博数据时出错: {str(e)}")
        raise

def nlp_douyin(temp_file):
    print(f"开始处理抖音数据: {temp_file}")
    try:
        df = pd.read_csv(temp_file)
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")

        def safe_sentiment(content):
            if pd.isna(content) or not isinstance(content, str):
                print(f"警告: 无效的内容类型 - {type(content)}, 值: {content}")
                return 0.5  # 默认中性情感
            try:
                return SnowNLP(str(content)).sentiments
            except Exception as e:
                print(f"情感分析错误: {str(e)}, 内容: {content}")
                return 0.5  # 出错时返回中性情感

        # 确保 '视频描述' 列存在
        content_column = '视频描述' if '视频描述' in df.columns else '内容'
        if content_column not in df.columns:
            print(f"警告: 找不到内容列 '{content_column}'")
            df['情感倾向'] = 0.5  # 如果找不到内容列，所有行都设置为中性
        else:
            df['情感倾向'] = df[content_column].apply(safe_sentiment)

        print("情感分析完成")
        print(f"情感分析结果的前几行:\n{df['情感倾向'].head()}")

        # 确保数值列为整数类型
        numeric_columns = ['点赞数', '评论数', '收藏数', '分享数']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        df.to_csv(temp_file, index=False, encoding='utf-8-sig')
        print(f"处理后的数据已保存到: {temp_file}")
        return

    except Exception as e:
        print(f"处理抖音数据时出错: {str(e)}")
        print(traceback.format_exc())


def main_weibo(keyword, max_page):
    print(f"开始爬取微博数据: 关键词={keyword}, 最大页数={max_page}")
    result = get_weibo_list(keyword, max_page)
    print(f"爬取完成，获取到 {len(result)} 条数据")
    
    temp_file = get_temp_file_path('weibo')
    print(f"将数据保存到临时文件: {temp_file}")
    
    df = pd.DataFrame(result)
    print(f"数据形状: {df.shape}")
    print(f"列名: {df.columns.tolist()}")
    df.to_csv(temp_file, index=False, encoding='utf-8-sig')
    
    print("开始进行情感分析")
    nlp_weibo(temp_file)
    
    # 保存到持久化文件
    persistent_file = get_persistent_file_path('微博', keyword)
    print(f"将数据保存到持久化文件: {persistent_file}")
    df.to_csv(persistent_file, index=False, encoding='utf-8-sig')
    
    print("微博数据处理完成")



def main_douyin(keyword, max_page):
    print(f"开始爬取抖音数据: 关键词={keyword}, 最大页数={max_page}")
    result = get_douyin_list(keyword, max_page)
    print(f"爬取完成，获取到 {len(result)} 条数据")
    
    temp_file = get_temp_file_path('douyin')
    print(f"将数据保存到临时文件: {temp_file}")
    
    df = pd.DataFrame(result)
    print(f"数据形状: {df.shape}")
    print(f"列名: {df.columns.tolist()}")
    df.to_csv(temp_file, index=False, encoding='utf-8-sig')
    return df


def normalize_gender(value):
    """标准化性别数据"""
    if pd.isna(value):
        return '未知'
    value = str(value).lower()
    if value in ['m', '男', 'male', '1']:
        return '男'
    elif value in ['f', '女', 'female', '2']:
        return '女'
    else:
        return '未知'

def process_platform_data(platforms, keyword):
    print(f"开始处理平台数据: platforms={platforms}, keyword={keyword}")
    
    dfs = []
    # 统一的列名映射，key为标准列名，value为各平台的原始列名
    unified_columns = {
        # 基础信息
        '用户名': {
            '微博': '微博作者',
            '抖音': '用户名'
        },
        '内容': {
            '微博': '微博内容',
            '抖音': '视频描述'
        },
        '发布时间': {
            '微博': '发布时间',
            '抖音': '发布时间'
        },
        
        # 互动数据
        '分享数': {
            '微博': '转发数',
            '抖音': '分享数'
        },
        '评论数': {
            '微博': '评论数',
            '抖音': '评论数'
        },
        '点赞数': {
            '微博': '点赞数',
            '抖音': '点赞数'
        },
        
        # ID和链接
        'uni_id': {
            '微博': '微博bid',
            '抖音': '视频id'
        },
        'url': {
            '微博': 'url',
            '抖音': 'url'
        },
        
        # 情感分析
        '情感倾向': {
            '微博': '情感倾向',
            '抖音': '情感倾向'
        },
        'sentiment_result': {
            '微博': 'sentiment_result',
            '抖音': 'sentiment_result'
        },
        
        # 性别信息
        '性别': {
            '微博': '性别',
            '抖音': '性别'
        },
        
        # 地理信息
        '省份': {
            '微博': '省份',
            '抖音': '省份'
        }
    }
    
    # 数值型列表
    numeric_columns = [
        '分享数', '评论数', '点赞数', '收藏数', 
        '用户关注数', '粉丝数', '抖音粉丝数', 
        '抖音关注数', '获赞数', '作品数', 
        '播放量', '商品数'
    ]
    
    for platform in platforms:
        try:
            persistent_file = get_persistent_file_path(platform, keyword)
            print(f"处理 {platform} 平台的数据，文件路径：{persistent_file}")
            
            if not os.path.exists(persistent_file):
                print(f"警告：{persistent_file} 不存在，跳过此平台")
                continue
            
            df = pd.read_csv(persistent_file)
            print(f"{platform} 数据形状：{df.shape}")
            print(f"{platform} 数据列名：{df.columns.tolist()}")
            
            # 创建新的DataFrame，使用统一的列名
            new_df = pd.DataFrame()
            
            # 遍历统一列名，进行映射
            for standard_col, platform_cols in unified_columns.items():
                if platform in platform_cols:
                    original_col = platform_cols[platform]
                    if original_col in df.columns:
                        new_df[standard_col] = df[original_col]
                    else:
                        # 如果是数值型列，填充0，否则填充空字符串
                        if standard_col in numeric_columns:
                            new_df[standard_col] = 0
                        else:
                            new_df[standard_col] = ''
                else:
                    # 该平台没有这个字段，填充默认值
                    if standard_col in numeric_columns:
                        new_df[standard_col] = 0
                    else:
                        new_df[standard_col] = ''
            
            # 标准化性别数据
            if '性别' in new_df.columns:
                new_df['性别'] = new_df['性别'].apply(normalize_gender)
            else:
                new_df['性别'] = '未知'
            
            # 添加平台标识列
            new_df['平台'] = platform
            
            # 确保数值列为整数类型
            for col in numeric_columns:
                if col in new_df.columns:
                    new_df[col] = pd.to_numeric(new_df[col], errors='coerce').fillna(0).astype(int)
            
            dfs.append(new_df)
            print(f"{platform} 数据处理完成")
            
        except Exception as e:
            print(f"处理 {platform} 数据时出错：{str(e)}")
            import traceback
            print(traceback.format_exc())
    
    if not dfs:
        print("没有成功处理任何平台的数据")
        return pd.DataFrame()
    
    try:
        # 合并所有平台的数据
        merged_df = pd.concat(dfs, ignore_index=True)
        print(f"合并后的数据形状：{merged_df.shape}")
        print(f"合并后的数据列名：{merged_df.columns.tolist()}")
        
        # 保存合并后的数据
        merged_df.to_csv(ready_path, index=False, encoding='utf-8-sig')
        print(f"合并后的数据已保存到：{ready_path}")
        
        return merged_df
        
    except Exception as e:
        print(f"合并数据时出错：{str(e)}")
        import traceback
        print(traceback.format_exc())
        return pd.DataFrame()




# def main_nlp(keyword, precision,platform):

def main_nlp(keyword, precision, platform):
    """
    主函数
    :param keyword: 关键词
    :param precision: 精确度
    :param platform: 平台
    :return:
    """
    try:
        # 设置最大页数
        if precision == '低':
            max_page = 5
        elif precision == '中':
            max_page = 10
        else:
            max_page = 15

        # 确保platform是列表格式
        if isinstance(platform, str):
            try:
                platforms = ast.literal_eval(platform)
            except (ValueError, SyntaxError):
                platforms = [platform]  # 如果解析失败，将其作为单个平台处理
        else:
            platforms = platform

        # 初始化计数器
        share_num = 0
        comment_num = 0
        like_num = 0
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        infos2_data = []

        # 遍历平台列表
        for p in platforms:
            if p == '微博':
                try:
                    main_weibo(keyword, max_page)
                except Exception as e:
                    print(f"微博爬取出错: {str(e)}")
                    continue

        # 读取并处理数据
        if os.path.exists(ready_path):
            try:
                df = pd.read_csv(ready_path, encoding='utf-8')
                
                # 确保所需列存在
                required_columns = ['微博id', '微博bid', '微博作者', '微博内容', '发布时间', '转发数', '评论数', '点赞数', 'url']
                for col in required_columns:
                    if col not in df.columns:
                        if col == '微博id':
                            df['微博id'] = df['微博bid'] if '微博bid' in df.columns else range(len(df))
                        else:
                            df[col] = 'N/A'
                
                # 处理数据
                for _, row in df.iterrows():
                    try:
                        info = {
                            '微博id': str(row['微博id']),
                            '用户名': str(row['微博作者']).strip() if pd.notna(row['微博作者']) else "未知作者",
                            '内容': str(row['微博内容']).strip() if pd.notna(row['微博内容']) else "无内容",
                            '发布时间': str(row['发布时间']).strip() if pd.notna(row['发布时间']) else "未知时间",
                            '分享数': int(row['转发数']) if pd.notna(row['转发数']) and str(row['转发数']).isdigit() else 0,
                            '评论数': int(row['评论数']) if pd.notna(row['评论数']) and str(row['评论数']).isdigit() else 0,
                            '点赞数': int(row['点赞数']) if pd.notna(row['点赞数']) and str(row['点赞数']).isdigit() else 0,
                            'url': str(row['url']) if pd.notna(row['url']) else ""
                        }
                        
                        # 更新计数
                        share_num += info['分享数']
                        comment_num += info['评论数']
                        like_num += info['点赞数']
                        
                        # 情感分析
                        sentiment = analyze_sentiment(info['内容'])
                        info['sentiment_result'] = sentiment
                        sentiment_counts[sentiment] += 1
                        
                        infos2_data.append(info)
                    except Exception as e:
                        print(f"处理数据行时出错: {str(e)}")
                        continue
            except Exception as e:
                print(f"读取CSV文件时出错: {str(e)}")
                
        return infos2_data, share_num, comment_num, like_num, sentiment_counts
    except Exception as e:
        print(f"执行main_nlp时出错: {str(e)}")
        raise

if __name__ == '__main__':
    # main_nlp('山东大学','low')
    dy_csv = 'dy_山东大学.csv'
    nlp_douyin(dy_csv)
    
