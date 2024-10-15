import atexit
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, Blueprint, request, session, jsonify
from model.nlp import get_info2,get_info3
import os
import csv
from model.ciyuntu import get_wordcloud_csv
from utils.info import *
from utils.get_tabledata import *
from utils.errorResponse import errorResponse
from spiders.pengpai import get_pengpai_list
from spiders.hotnews import *
import random
from utils.common import update_persistent_file,get_persistent_file_path,get_temp_file_path
from utils.tools import dynamic_spider_task

# 全局变量
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


pb = Blueprint('page',__name__,url_prefix='/page',template_folder='templates')
ready_path = get_persistent_file_path('all','any')
# 全局字典来存储每个任务的状态
task_status = {}
def run_wordcloud_task(csv_path, task_id):
    try:
        get_wordcloud_csv(csv_path)
        task_status[task_id] = "completed"
    except Exception as e:
        task_status[task_id] = f"error: {str(e)}"
    finally:
        scheduler.remove_job(task_id)

@pb.route('/home')
def home():
    users = session.get('username')
    unique_user_count, total_heat_value, unique_ip_count, row_count = fenxi()
    try:
        infos2_data = get_info3(ready_path)
    except Exception as e:
        return errorResponse(e)
    current_date = datetime.now().strftime('%Y%m%d')
    csv_file_name = f'{current_date}_pengpai.csv'
    images_dir = 'E:\\python\\flaskProject\\static\\content\\'+f'{csv_file_name}'

    # 检查文件是否存在
    if os.path.exists(images_dir):
        print(f"文件 {csv_file_name} 存在，正在读取...")
        daily_hotspots = []
        with open(images_dir, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                daily_hotspots.append({
                    'title': row['标题'],
                    'cover_image': row['封面链接'],  # 保存相对路径
                    'source': row['发文者'],
                    'link': row['链接'],
                    'read_link': row['down_link']
                })
    else:
        daily_hotspots = get_pengpai_list()
    return render_template('index.html',
                           user_name=users,
                           row_count=row_count,
                           unique_user_count=unique_user_count,
                           total_heat_value=total_heat_value,
                           unique_ip_count=unique_ip_count,
                           infos2_data = infos2_data,
                           daily_hotspots = daily_hotspots
                           )

@pb.route('/setting_spider',methods=['GET','POST'])
def setting_spider():
    if request.method == "GET":
        try:
            infos2, share_num, comment_num, like_num = get_info2('weibo_temp.csv')
        except Exception as e:
            share_num = 0
            comment_num = 0
            like_num = 0
            infos2 = []
            print(e)
        # 检查 share_num 是否为空（None 或者其他表示空值的形式），如果是，则设置为 999
        share_num = share_num if share_num else 0
        comment_num = comment_num if comment_num else 0
        like_num = like_num if like_num else 0
        pie_data = {
            '转发数': share_num,
            '点赞数': like_num,
            '评论数': comment_num
        }
        try:
            history_records = []
            with open('memory.csv', 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # 处理平台字段，将字符串转换为列表
                    row['platform'] = eval(row['平台'])
                    history_records.append({
                        'timestamp': row['时间'],
                        'platform': ', '.join(row['platform']),  # 将列表转换为逗号分隔的字符串
                        'keyword': row['关键词'],
                        'start_date': row['开始时间'],
                        'end_date': row['截止时间'],
                        'precision': row['精度']
                    })
        except:
            history_records = []


        try:
            df_sentiment = pd.read_csv('weibo_temp.csv')
            if 'sentiment_result' not in df_sentiment.columns:
                neutral_count = 0
                positive_count = 0
                negative_count = 0
                exit()
            # 统计“正面”、“负面”、“中性”的数量
            sentiment_counts = df_sentiment['情感倾向'].value_counts()
            # 如果想要单独打印各个情感的数量
            positive_count = sentiment_counts.get('正面', 0)
            negative_count = sentiment_counts.get('负面', 0)
            neutral_count = sentiment_counts.get('中性', 0)
        except:
            neutral_count = 0
            positive_count = 0
            negative_count = 0
        finally:
            neutral_count = neutral_count if neutral_count else 0
            positive_count  = positive_count if positive_count else 0
            negative_count = negative_count if negative_count else 0

        return render_template('spider_setting.html',
                               # user_name=users,
                               infos2=infos2,
                               share_num = share_num,
                               comment_num = comment_num,
                               like_num = like_num,
                               pie_data=pie_data,
                               positive_count = positive_count,
                               negative_count = negative_count,
                               neutral_count = neutral_count,
                               history_records = history_records
                               )
    elif request.method == "POST":
        keyword = request.form.get('keyword')
        platforms = request.form.getlist('platforms[]')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        precision = request.form.get('precision')

        mapping_dict = {
            'douyin': '抖音',
            'weibo': '微博',
            'bilibili': '哔哩哔哩'
        }

        mapping2_dict = {
            'low': '低',
            'medium': '中',
            'high': '高'
        }

        platforms = [mapping_dict.get(item, item) for item in platforms]

        precision = mapping2_dict.get(precision, precision)

        # 表头信息
        memory_headers = ["时间", "平台", "关键词", "开始时间",'截止时间', "精度"]
        # 创建CSV文件并写入表头

        # 判断文件是否存在
        file_exists = os.path.exists('memory.csv')

        # 创建CSV文件并写入表头（如果文件不存在）
        with open('memory.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # 如果文件不存在，则写入表头
            if not file_exists:
                writer.writerow(memory_headers)
            # 获取当前时间
            now = datetime.now()
            # 格式化输出，精确到分钟
            formatted_now = str(now.strftime('%Y-%m-%d %H:%M'))
            data_rows = [
                [formatted_now, platforms, keyword, start_date,end_date, precision],
            ]
            writer.writerows(data_rows)
        history_records = []
        with open('memory.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # 处理平台字段，将字符串转换为列表
                row['platform'] = list(row['平台'])
                history_records.append({
                    'timestamp': row['时间'],
                    'platform': ''.join(row['platform']),  # 将列表转换为逗号分隔的字符串
                    'keyword': row['关键词'],
                    'start_date': row['开始时间'],
                    'end_date': row['截止时间'],
                    'precision': row['精度']
                })

        csv_path = f"{keyword}.csv"
        print(platforms)
        platforms = list(platforms)
        print(platforms)
        try:
            infos2, share_num, comment_num,like_num,sentiment_counts = dynamic_spider_task(keyword, platforms, start_date, end_date, precision)
            print(f"动态爬虫任务已启动: {keyword}")
        except Exception as e:
            print(f"启动动态爬虫任务时出错: {str(e)}")

        positive_count = sentiment_counts.get('正面', 0)
        negative_count = sentiment_counts.get('负面', 0)
        neutral_count = sentiment_counts.get('中性', 0)
        # infos2, share_num, comment_num, like_num = get_info2(csv_path)
        # 生成一个从100000到999999之间的随机整数
        random_six_digit_number = random.randint(100000, 999999)

        task_id = f"{keyword}_{random_six_digit_number}"

        # 使用 APScheduler 添加任务
        scheduler.add_job(
            run_wordcloud_task,
            args=[csv_path, task_id],
            id=task_id,
            replace_existing=True
        )

        share_num = share_num if share_num else 0
        comment_num = comment_num if comment_num else 0
        like_num = like_num if like_num else 0
        pie_data = {
            '转发数': share_num,
            '点赞数': like_num,
            '评论数': comment_num
        }
        return render_template('spider_setting.html',
                               infos2=infos2,
                               share_num=share_num,
                               comment_num=comment_num,
                               like_num=like_num,
                               pie_data=pie_data,
                               positive_count=positive_count,
                               negative_count=negative_count,
                               neutral_count=neutral_count,
                               task_id=task_id,
                               history_records = history_records
                               )


@pb.route('/tableData')
def tableData():
    users = session.get('username')
    return render_template('bigdata.html',
                           user_name=users,
                           )

@pb.route('/q_a')
def q_a():
    users = session.get('username')
    return render_template('question_answer.html',
                           user_name=users,
                           )

@pb.route('/table')
def table():
    users = session.get('username')
    comments_data = get_info()
    unique_user_count, total_heat_value, unique_ip_count, row_count = fenxi()
    return render_template('bigdata.html',
                           user_name=users,
                           row_count=row_count,
                           unique_user_count=unique_user_count,
                           total_heat_value=total_heat_value,
                           unique_ip_count=unique_ip_count,
                           comments_data=comments_data)


@pb.route('/api/chart-data')
def get_chart_data():
    try:
        df_sentiment = pd.read_csv(ready_path)
        if '情感倾向' not in df_sentiment.columns:
            raise ValueError("sentiment_result column not found in CSV")

         # 根据新的标准重新分类情感倾向
        def classify_sentiment(value):
            try:
                value = float(value)
                if value < 0.3:
                    return '负面'
                elif value > 0.7:
                    return '正面'
                else:
                    return '中性'
            except ValueError:
                return '中性'  # 如果无法转换为浮点数,默认为中性

        df_sentiment['情感倾向'] = df_sentiment['情感倾向'].apply(classify_sentiment)

        # 统计新的情感倾向分布
        sentiment_counts = df_sentiment['情感倾向'].value_counts()
        gender_count = df_sentiment['性别'].value_counts()

        # 使用 get 方法并提供默认值 0
        positive_count = int(sentiment_counts.get('正面', 0))
        negative_count = int(sentiment_counts.get('负面', 0))
        neutral_count = int(sentiment_counts.get('中性', 0))
        male_count = int(gender_count.get('m', 0))
        female_count = int(gender_count.get('f', 0))

        # 对省份进行计数
        province_counts = df_sentiment['省份'].value_counts().to_dict()
        heatmap_data = [
            {
                "name": province,
                "value": int(value)
            }
            for province, value in province_counts.items()
        ]

        sentiment_data = {
            '正面': positive_count,
            '负面': negative_count,
            '中性': neutral_count
        }
        gender_data = {
            '男': male_count,
            '女': female_count
        }

        return jsonify({
            'heatmapData': heatmap_data,
            'sentimentData': sentiment_data,
            'genderData': gender_data
        })

    except Exception as e:
        print(f"Error in get_chart_data: {str(e)}")
        return jsonify({
            'error': 'An error occurred while processing the data',
            'details': str(e)
        }), 500

@pb.route('/api/hot-topics')
def get_hot_topics():
    try:
        topics = get_hot_dy()
        return jsonify(topics)
    except Exception as e:
        print(f"Error in get_hot_topics: {str(e)}")
        return jsonify({
            'error': 'An error occurred while fetching hot topics',
            'details': str(e)
        }), 500

@pb.route('/api/realtime-monitoring')
def get_realtime_monitoring():
    df = pd.read_csv(ready_path, encoding='utf-8')
    selected_columns = ['微博作者', '微博内容', 'url']
    selected_df = df[selected_columns]
    json_data = []
    for index, row in selected_df.iterrows():
        # 检查并处理NaN值
        author = row['微博作者'] if pd.notna(row['微博作者']) else "未知作者"
        content = row['微博内容'] if pd.notna(row['微博内容']) else "无内容"
        url = row['url'] if pd.notna(row['url']) else "#"
        
        json_data.append({
            "author": author,
            "content": content,
            "authorLink": url
        })
    
    # 使用ensure_ascii=False来正确处理中文字符
    return json.dumps(json_data, ensure_ascii=False, indent=2)



@pb.route('/stop_spider_task', methods=['POST'])
def stop_spider_task():
    jobs = scheduler.get_jobs()
    for job in jobs:
        scheduler.remove_job(job.id)
    task_status.clear()  # 清空任务状态字典
    return jsonify({
        "message": "所有定时任务已停止",
        "status": "success"
    }), 200


@pb.route('/api/status')
def get_task_status():
    jobs = scheduler.get_jobs()
    task_info = []
    for job in jobs:
        print(f"找到任务: {job.id}, 下次运行时间: {job.next_run_time}")
        task_info.append({
            "id": job.id,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "status": task_status.get(job.id, "running")
        })

    if jobs:
        next_time = jobs[0].next_run_time
        # 将 datetime 对象转换为字符串
        next_time_str = next_time.isoformat()
        next_time_str = next_time_str.replace('T', ' ')
        next_time_str = next_time_str[:19]
        message = f"正在执行定时任务,下次运行时间{next_time_str}"
        status = "working"
    else:
        message = "当前没有正在执行的任务"
        status = "idle"

    print(f"任务状态: {message}, 任务数: {len(jobs)}")
    return jsonify({
        "message": message,
        "status": status,
        "tasks": task_info
    })




