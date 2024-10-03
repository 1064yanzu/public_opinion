import os
import traceback

from snownlp import SnowNLP
import pymysql
import pandas as pd
from datetime import datetime
import ast
from utils.common import update_persistent_file,get_persistent_file_path,get_temp_file_path
from spiders.articles_spider import get_weibo_list
from spiders.douyin import get_douyin_list


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

def get_info2_mysql() :
    # 连接到MySQL数据库
    conn = pymysql.connect(
      host="localhost",
      user="root",
      password="123456",
      database='weiboarticles',
      charset='utf8mb4',
    )

    # 使用Pandas执行SQL查询
    sql_query = "SELECT 微博作者,微博内容,转发数,发布时间,评论数,点赞数 FROM weibo_spider"
    df = pd.read_sql(sql_query, conn)
    # 将DataFrame转换为字典列表
    infos2_data = df.to_dict(orient='records')

    # 使用Pandas执行SQL查询
    sql_query = "SELECT 转发数, 评论数, 点赞数 FROM weibo_spider"
    df = pd.read_sql(sql_query, conn)

    # 检查查询结果是否为空
    if df.empty:  # 如果DataFrame为空
        # 直接返回默认值0
        return [],0,0,0
    else:
        # 对各列进行求和
        summary = df.sum(numeric_only=True)  # numeric_only=True确保只对数值型列求和

        # 确保即使在极端情况下（比如某列在数据库中无数据）也能安全访问
        share_num = summary.get('转发数', 0)
        comment_num = summary.get('评论数', 0)
        like_num = summary.get('点赞数', 0)

    return infos2_data,share_num,comment_num,like_num

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

def get_ip(csv_path ='E:\\python\\flaskProject\\model\\database.csv'):
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

def target_file2_mysql():
    # 创建数据库连接
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='123456',
                                 database='weiboarticles',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # 获取所有评论
            sql = "SELECT `微博id`, `微博内容` FROM `weibo_spider`"
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                comment_id = row['微博id']
                content = row['微博内容']
                sentiment_value = SnowNLP(content).sentiments
                sentiment = '正面' if sentiment_value > 0.5 else '负面' if sentiment_value < 0.5 else '中性'
                update_sql = f"UPDATE `comments` SET `sentiment_result` = '{sentiment}' WHERE `id` = {comment_id}"
                cursor.execute(update_sql)
            # 提交事务，确保更改被保存到数据库
            connection.commit()

    finally:
        connection.close()


def nlp_weibo(csv_path):
    # # 读取CSV文件
    # df = pd.read_csv(csv_path)

    # # 获取当前时间
    # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # # 初始化情感统计
    # global sentiments
    # sentiments = []
    # global sentiment_counts
    # sentiment_counts = {'正面': 0, '负面': 0, '中性': 0}

    # # 对每条微博记录进行情感分析
    # for _, row in df.iterrows():
    #     content = str(row['微博内容'])
    #     sentiment_value = SnowNLP(content).sentiments
    #     sentiment = '正面' if sentiment_value > 0.6 else '负面' if sentiment_value < 0.3 else '中性'

    #     # 更新情感计数器
    #     sentiment_counts[sentiment] += 1

    #     # 添加情感结果到DataFrame
    #     df.at[_, 'sentiment_result'] = sentiment

    #     # 添加爬取时间到DataFrame
    #     df.at[_, 'crawl_time'] = current_time  # 添加当前时间为爬取时间

    #     sentiments.append(sentiment)
    # if csv_path == 'weibo_temp.csv':
    #     df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    # else:
    #     # 将更新后的数据写回CSV文件
    #     df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    #     df.to_csv('E:\\python\\flaskProject\\model\\database.csv', index=False, encoding='utf-8-sig')
    #     return sentiments, sentiment_counts
    print(f"开始处理微博数据: {csv_path}")
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

    df['情感倾向'] = df['微博内容'].apply(safe_sentiment)
    
    print("情感分析完成")
    print(f"情感分析结果的前几行:\n{df['情感倾向'].head()}")
    
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    df.to_csv('E:\\python\\flaskProject\\model\\database.csv', index=False, encoding='utf-8-sig')
    print(f"处理后的数据已保存到: {csv_path}")



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


def process_platform_data(platforms, keyword):
    print(f"开始处理平台数据: platforms={platforms}, keyword={keyword}")
    
    dfs = []
    column_mapping = {
        '微博': {
            '微博作者': '用户名',
            '微博内容': '内容',
            '转发数': '分享数',
            '评论数': '评论数',
            '点赞数': '点赞数',
            '情感倾向': '情感倾向',
            'crawl_time': '爬取时间',
            'url': 'url',
            # '微博bid': 'uni_id',
            '发布时间': '发布时间'
        },
        '抖音': {
            '用户名': '用户名',
            '视频描述': '内容',
            '分享数': '分享数',
            '评论数': '评论数',
            '点赞数': '点赞数',
            '情感倾向': '情感倾向',
            'crawl_time': '爬取时间',
            'url': 'url',
            # 'aweme_id': 'uni_id',
            '发布时间': '发布时间'
        }
    }
    
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
            
            # 重命名列
            df = df.rename(columns=column_mapping[platform])
            print(f"{platform} 重命名后的列名：{df.columns.tolist()}")
            
            # 添加平台列
            df['平台'] = platform
            
            dfs.append(df)
        except Exception as e:
            print(f"处理 {platform} 数据时出错：{str(e)}")
            import traceback
            print(traceback.format_exc())
    
    if not dfs:
        print("没有成功处理任何平台的数据")
        return pd.DataFrame()
    
    try:
        merged_df = pd.concat(dfs, ignore_index=True)
        print(f"合并后的数据形状：{merged_df.shape}")
        print(f"合并后的数据列名：{merged_df.columns.tolist()}")
        
        # 选择需要保留的列
        final_columns = ['平台', '用户名', '内容', '分享数', '评论数', '点赞数', '情感倾向', '爬取时间', 'url', 'uni_id', '发布时间']
        existing_columns = [col for col in final_columns if col in merged_df.columns]
        merged_df = merged_df[existing_columns]
        
        # 确保数值列为数值类型
        numeric_columns = ['分享数', '评论数', '点赞数']
        for col in numeric_columns:
            if col in merged_df.columns:
                merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0).astype(int)
        
        # 保存合并后的数据
        output_file = f'merged_{keyword}.csv'
        merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"合并后的数据已保存到：{output_file}")
        print(f"最终数据列名：{merged_df.columns.tolist()}")
        
        return merged_df
    except Exception as e:
        print(f"合并数据时出错：{str(e)}")
        import traceback
        print(traceback.format_exc())
        return pd.DataFrame()




# def main_nlp(keyword, precision,platform):

def main_nlp(keyword, precision, platform):
    print(f"执行 main_nlp: keyword={keyword}, precision={precision}, platform={platform}")
    
    if precision == '低':
        max_page = 5
    elif precision == '中':
        max_page = 10
    else:
        max_page = 15

    try:
        platforms = ast.literal_eval(platform)
        if isinstance(platforms, str):
            platforms = [platforms]
    except:
        platforms = [platform] if isinstance(platform, str) else platform

    print(f"处理的平台: {platforms}")
    weibo_is = 0
    douyin_is = 0
    for p in platforms:
        if p == '微博':
            main_weibo(keyword, max_page)
            weibo_is = 1
        elif p == '抖音':
            main_douyin(keyword, max_page)
            douyin_is = 1

    try:
        if weibo_is == 1:
            print("微博数据处理完成")
            read_file = get_persistent_file_path('微博', keyword)
            df = pd.read_csv(read_file)
            infos2_data = df.to_dict(orient='records')
            share_num = int(df['分享数'].sum())
            comment_num = int(df['评论数'].sum())
            like_num = int(df['点赞数'].sum())
            sentiment_counts = df['情感倾向'].value_counts().to_dict()
        elif douyin_is == 1:
            read_file = get_persistent_file_path('抖音', keyword)
            df = pd.read_csv(read_file)
            infos2_data = df.to_dict(orient='records')
            share_num = int(df['分享数'].sum())
            comment_num = int(df['评论数'].sum())
            like_num = int(df['点赞数'].sum())
            sentiment_counts = df['情感倾向'].value_counts().to_dict()
        
        print(f"处理后的数据类型: infos2_data: {type(infos2_data)}, 长度: {len(infos2_data)}")
        print(f"share_num: {type(share_num)}, 值: {share_num}")
        print(f"comment_num: {type(comment_num)}, 值: {comment_num}")
        print(f"like_num: {type(like_num)}, 值: {like_num}")
        print(f"sentiment_counts: {type(sentiment_counts)}, 值: {sentiment_counts}")
        
        return infos2_data, share_num, comment_num, like_num, sentiment_counts
    except Exception as e:
        print(f"处理平台数据时出错: {str(e)}")
        print(traceback.format_exc())
    try:
        platforms = ast.literal_eval(platform)
        if isinstance(platforms, str):
            print(4)
            platforms = [platforms]
            # 对每个平台执行相应的函数
            for p in platforms:
                if p == '微博':
                    main_weibo(keyword, max_page)
                elif p == '抖音':
                    main_douyin(keyword, max_page)

    except:
        print(platform[0])
        if platform[0] == '微博':
            print('微博p')
            main_weibo(keyword, max_page)
        elif platform[0] == '抖音':
            print('抖音1')
            main_douyin(keyword, max_page)
        else:
            print('不满足')

    process_platform_data(platforms,keyword)
    infos2_data, share_num, comment_num, like_num,sentiment_counts = get_info2(f'merged_{keyword}.csv')
    return infos2_data, share_num, comment_num,like_num,sentiment_counts

if __name__ == '__main__':
    # main_nlp('山东大学','low')
    dy_csv = 'dy_山东大学.csv'
    nlp_douyin(dy_csv)
    
