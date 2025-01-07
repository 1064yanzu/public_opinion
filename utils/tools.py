from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import time, timedelta, datetime
from utils.common import update_persistent_file
import numpy as np
import pandas as pd
import os
from model.nlp import main_nlp
from utils.common import get_temp_file_path,get_persistent_file_path



time_intervals = {
    "morning": {"start": time(6, 0), "end": time(12, 0), "interval": 30},
    "afternoon": {"start": time(12, 0), "end": time(18, 0), "interval": 45},
    "evening": {"start": time(18, 0), "end": time(22, 0), "interval": 60},
    "night": {"start": time(22, 0), "end": time(6, 0), "interval": 120}
}


def get_current_interval():
    now = datetime.now().time()
    interval = None  # 默认值为 None

    # 遍历时间段及其设置
    for period, settings in time_intervals.items():
        start_time = settings["start"]
        end_time = settings["end"]

        # 处理跨天的情况
        if start_time > end_time:
            if now >= start_time or now < end_time:
                interval = settings["interval"]
                break
        else:
            if start_time <= now < end_time:
                interval = settings["interval"]
                break
    return interval


def dynamic_spider_task(keyword, platforms, start_date, end_date, precision):
    print(f"开始执行动态爬虫任务: keyword={keyword}, platforms={platforms}, start_date={start_date}, end_date={end_date}, precision={precision}")
    
    try:
        # 获取当前时间段的间隔时间
        interval = get_current_interval()
        if interval is None:
            print("警告: 无法获取当前时间段的间隔时间，使用默认值60分钟")
            interval = 60
        print(f"当前间隔时间: {interval}分钟")

        # 执行爬虫任务并获取数据
        infos2_data, share_num, comment_num, like_num, sentiment_counts = main_nlp(keyword, precision, platforms)
        
        print(f"main_nlp 返回数据类型:")
        print(f"infos2_data: {type(infos2_data)}, 长度: {len(infos2_data) if isinstance(infos2_data, (list, dict)) else 'N/A'}")
        print(f"share_num: {type(share_num)}, 值: {share_num}")
        print(f"comment_num: {type(comment_num)}, 值: {comment_num}")
        print(f"like_num: {type(like_num)}, 值: {like_num}")
        print(f"sentiment_counts: {type(sentiment_counts)}, 值: {sentiment_counts}")

        # 计算下次执行时间
        next_run_time = datetime.now() + timedelta(minutes=interval)
        print(f"下次执行时间: {next_run_time}")

        # 使用全局scheduler添加下一次任务
        from views.page.page import scheduler
        job_id = f'spider_job_{keyword}'
        
        # 如果已存在相同ID的任务，先移除它
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # 添加新的定时任务
        scheduler.add_job(
            func=dynamic_spider_task,
            trigger='date',
            run_date=next_run_time,
            args=[keyword, platforms, start_date, end_date, precision],
            id=job_id,
            replace_existing=True
        )
        print(f"成功添加下一次任务: {job_id}")

        # 更新数据文件
        csv_2 = 'weibo_temp.csv'
        csv_1 = f'{keyword}.csv'
        update_database(csv_1, csv_2)

        # 转换数据类型并返回
        return to_python_type(infos2_data), to_python_type(share_num), to_python_type(comment_num), to_python_type(like_num), to_python_type(sentiment_counts)
    except Exception as e:
        print(f"动态爬虫任务执行出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise


def to_python_type(data):
    """将数据结构中的 numpy 类型转换为 Python 基础类型"""
    if isinstance(data, dict):
        return {k: to_python_type(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [to_python_type(item) for item in data]
    elif isinstance(data, (
    np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(data)
    elif isinstance(data, (np.float_, np.float16, np.float32, np.float64)):
        return float(data)
    elif isinstance(data, (np.complex_, np.complex64, np.complex128)):
        return complex(data)
    else:
        return data


def update_database(csv_1, csv_2):
    """
    更新数据库
    :param csv_1: 现有数据文件路径
    :param csv_2: 新数据文件路径
    :return: None
    """
    try:
        # 读取现有数据和新数据
        existing_data = pd.read_csv(csv_1) if os.path.exists(csv_1) else pd.DataFrame()
        new_df = pd.read_csv(csv_2)
        
        # 确保两个DataFrame都有必要的列
        required_columns = ['微博id', '微博bid', '微博作者', '微博内容', '发布时间', '转发数', '评论数', '点赞数', 'url']
        
        # 处理现有数据
        if not existing_data.empty:
            for col in required_columns:
                if col not in existing_data.columns:
                    if col == '微博id':
                        # 如果没有微博id列，使用微博bid作为id
                        existing_data['微博id'] = existing_data['微博bid'] if '微博bid' in existing_data.columns else range(len(existing_data))
                    else:
                        existing_data[col] = 'N/A'
        
        # 处理新数据
        for col in required_columns:
            if col not in new_df.columns:
                if col == '微博id':
                    # 如果没有微博id列，使用微博bid作为id
                    new_df['微博id'] = new_df['微博bid'] if '微博bid' in new_df.columns else range(len(new_df))
                else:
                    new_df[col] = 'N/A'
        
        # 合并数据
        if existing_data.empty:
            merged_df = new_df
        else:
            # 使用微博id作为索引合并数据
            merged_df = pd.concat([existing_data, new_df]).drop_duplicates(subset=['微博id'], keep='last')
        
        # 保存合并后的数据
        merged_df.to_csv(csv_1, index=False, encoding='utf-8-sig')
        print(f"数据库更新成功，保存到: {csv_1}")
        
    except Exception as e:
        print(f"更新数据库时出错: {str(e)}")
        raise


def update_database_douyin(DATABASE_PATH, new_data):
    # 读取现有数据
    if os.path.exists(DATABASE_PATH):
        existing_data = pd.read_csv(DATABASE_PATH)
    else:
        existing_data = pd.DataFrame(
            columns=['视频id', '视频描述', '播放量', '点赞数', '评论数', '收藏数', '分享数', '用户名', '用户id', '粉丝数',
                     '关注数', '获赞数', 'sentiment_result', '爬取时间'])

    # 将新数据转换为DataFrame，并添加爬取时间
    new_df = pd.read_csv(new_data)
    new_df['爬取时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 合并数据，使用'视频id'作为键，更新指定字段
    merged_df = existing_data.set_index('视频id').combine_first(new_df.set_index('视频id')).reset_index()

    # 更新指定字段
    fields_to_update = ['视频描述', '播放量', '点赞数', '评论数', '收藏数', '分享数', '用户名', '用户id', '粉丝数',
                        '关注数', '获赞数', 'sentiment_result', '爬取时间']
    for field in fields_to_update:
        merged_df.loc[merged_df.index.isin(new_df.index), field] = new_df[field]

    # 按爬取时间降序排序
    merged_df = merged_df.sort_values(by='爬取时间', ascending=False)
    
    # 保存更新后的数据
    merged_df.to_csv(DATABASE_PATH, index=False)





def update_persistent_file(persistent_file, temp_file):
    """更新持久文件"""
    if not os.path.exists(persistent_file):
        # 如果持久文件不存在，直接将临时文件复制为持久文件
        pd.read_csv(temp_file).to_csv(persistent_file, index=False)
    else:
        # 读取现有的持久文件和临时文件
        existing_df = pd.read_csv(persistent_file)
        new_df = pd.read_csv(temp_file)
        
        # 合并数据，使用'uni_id'作为键，更新指定字段
        merged_df = pd.concat([existing_df, new_df]).drop_duplicates(subset='uni_id', keep='last')
        
        # 保存更新后的数据
        merged_df.to_csv(persistent_file, index=False)