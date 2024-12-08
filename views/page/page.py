import atexit
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, Blueprint, request, session, jsonify, Response, stream_with_context
from model.nlp import get_info2,get_info3
import csv
from model.ciyuntu import get_wordcloud_csv
from utils.info import *
from utils.get_tabledata import *
from spiders.pengpai import get_pengpai_list
from spiders.hotnews import *
import random
from utils.common import update_persistent_file,get_persistent_file_path,get_temp_file_path
from utils.tools import dynamic_spider_task
import pandas as pd
import zhipuai
import json
import time
from utils.report_generator import ReportGenerator
import os
import traceback  # 添加这个用于详细错误追踪
from config.settings import ZHIPUAI_API_KEY, MODEL_CONFIG, REPORT_CONFIG

# 全局变量
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())
# 获取当前文件的绝对路径
current_file_path = __file__
# 获取当前文件的父目录的父目录
parent_parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))

pb = Blueprint('page',__name__,url_prefix='/page',template_folder='templates')
ready_path = get_persistent_file_path('all','any')
# 全局字典来存储每个任务的状
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
        infos2_data = []
        # return errorResponse(e)
    current_date = datetime.now().strftime('%Y%m%d')
    csv_file_name = f'{current_date}_pengpai.csv'
    # 拼接目标目录路径
    target_dir = os.path.join(parent_parent_dir, 'static', 'content')
    images_dir = target_dir+f'{csv_file_name}'

    # 检查文件是否存在
    if (os.path.exists(images_dir)):
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
        try:
            daily_hotspots = get_pengpai_list()
        except:
            daily_hotspots = []
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
            infos2, share_num, comment_num, like_num = get_info2(ready_path)
        except Exception as e:
            share_num = 0
            comment_num = 0
            like_num = 0
            infos2 = []
            print(e)
        # 检查 share_num 是否为空（None 或者其他表示空值的形式），如果是则设置为 999
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
            # 统计"正面"、"负面"、"中性"的数量
            sentiment_counts = df_sentiment['情感倾向'].value_counts()
            # 如果想要单独打印各情感的数量
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
            # 格式化输出精确到秒
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
                    'platform': ''.join(row['平台']),  # 将列表转换为逗号分隔的字符串
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
            print(f"启动动态爬任务错: {str(e)}")

        positive_count = sentiment_counts.get('正面', 0)
        negative_count = sentiment_counts.get('负面', 0)
        neutral_count = sentiment_counts.get('中性', 0)
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


@pb.route('/settle')
def settle():
    return render_template('settle.html')

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
            raise ValueError("情感倾向列在CSV中未找到")

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
                return '中性'  # 如果无法转换为浮点数,默认���中性

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
            'error': '处理数据时发生错误',
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
    selected_columns = ['微博作者', '微博内容', 'url','主页']
    selected_df = df[selected_columns]
    json_data = []
    for index, row in selected_df.iterrows():
        # 检查并处理NaN值
        author = row['微博作者'] if pd.notna(row['微博作者']) else "未知作者"
        content = row['微博内容'] if pd.notna(row['微博内容']) else "无内容"
        url = row['url'] if pd.notna(row['url']) else "#"
        author_url = row['主页'] if pd.notna(row['主页']) else "#"
        json_data.append({
            "author": author,
            "content": content,
            "Link": url,
            "authorUrl": author_url
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

@pb.route('/api/stats')
def get_stats():
    """获取实时统计数据"""
    print("\n=== 开始获取统计数据 ===")
    print(f"CSV文件路径: {ready_path}")
    print(f"文件是否存在: {os.path.exists(ready_path)}")
    
    try:
        if not os.path.isfile(ready_path):
            print("错误: 文件不存在")
            return jsonify({
                'todayMonitor': 0,
                'totalComments': 0,
                'heatIndex': 0,
                'riskLevel': '低'
            })

        try:
            print("尝试读取CSV文件...")
            df = pd.read_csv(ready_path, encoding='utf-8')
            print(f"成功读取CSV文件，数据行数: {len(df)}")
            print(f"列名: {df.columns.tolist()}")
        except UnicodeDecodeError:
            print("UTF-8编码失败，尝试GBK编码...")
            df = pd.read_csv(ready_path, encoding='gbk')
            print("使用GBK编码成功读取")
        except Exception as e:
            print(f"读取CSV文件失败: {str(e)}")
            raise

        print("\n开始处理数据...")
        df['发布时间'] = pd.to_datetime(df['发布时间'], errors='coerce')
        today = datetime.now().strftime('%Y-%m-%d')
        today_data = df[df['发布时间'].dt.strftime('%Y-%m-%d') == today]
        print(f"今日数据量: {len(today_data)}")

        # 处理数值列
        numeric_columns = ['评论数', '转发数', '点赞数']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            print(f"{col}总和: {df[col].sum()}")

        result = {
            'todayMonitor': int(len(today_data)),
            'totalComments': int(df['评论数'].sum()),
            'heatIndex': int((df['转发数'].sum() * 0.4 + 
                            df['评论数'].sum() * 0.3 + 
                            df['点赞数'].sum() * 0.3) / 100),
            'riskLevel': calculate_risk_level(df)
        }

        print("\n=== 返回数据 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return jsonify(result)

    except Exception as e:
        print("\n=== 发生错误 ===")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print("详细错误栈:")
        print(traceback.format_exc())
        return jsonify({
            'todayMonitor': 0,
            'totalComments': 0,
            'heatIndex': 0,
            'riskLevel': '低'
        })

@pb.route('/api/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        depth = data.get('depth', 'standard')
        
        if not os.path.exists(ready_path):
            return jsonify({'error': 'CSV文件不存在'}), 404
            
        generator = ReportGenerator(ready_path)
        
        def generate():
            try:
                current_section = "summary"
                sections = {
                    'summary': [],
                    'analysis': [],
                    'suggestions': [],
                    'risks': []
                }
                
                for chunk in generator.generate_stream(depth):
                    if chunk.get('code') != 200:
                        yield json.dumps({'error': chunk.get('msg', '未知错误')}) + '\n'
                        return
                        
                    content = chunk.get('data', {}).get('text', '')
                    if content:
                        # 根据内容判断当前章节
                        if "舆情分析" in content:
                            current_section = "analysis"
                        elif "应对建议" in content:
                            current_section = "suggestions"
                        elif "风险提示" in content:
                            current_section = "risks"
                            
                        sections[current_section].append(content)
                        yield json.dumps({
                            'type': current_section,
                            'content': content
                        }) + '\n'
                
                # 生成完整报告
                final_report = {
                    'type': 'complete',
                    'sections': {
                        'summary': ''.join(sections['summary']),
                        'analysis': ''.join(sections['analysis']),
                        'suggestions': [s.strip() for s in ''.join(sections['suggestions']).split('\n') if s.strip()],
                        'risks': ''.join(sections['risks'])
                    }
                }
                yield json.dumps(final_report) + '\n'
                        
            except Exception as stream_error:
                yield json.dumps({'error': f"生成报告失败: {str(stream_error)}"}) + '\n'
                
        return Response(
            stream_with_context(generate()),
            mimetype='application/x-ndjson',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        return jsonify({'error': f"请求处理失败: {str(e)}"}), 500

@pb.route('/api/realtime_data')
def get_realtime_data():
    """获取实时舆情数据"""
    try:
        df = pd.read_csv(ready_path)
        
        # 计算涉及的省份数量
        province_count = df['省份'].nunique()
        
        # 根据省份数量判断传播范围
        if province_count > 20:
            spread_range = "全国性传播"
        elif province_count > 10:
            spread_range = "区域性传播"
        else:
            spread_range = "局部传播"

        result = {
            'latestComment': str(df.iloc[-1]['微博内容']) if len(df) > 0 else "暂无数据",
            'commentTime': str(df.iloc[-1]['发布时间']) if len(df) > 0 else "暂无数据",
            'provinceCount': f"{province_count}个",
            'spreadRange': spread_range,
            'keywords': ['热点话题', '用户反馈', '社会关注', '热门事件', '公众讨论'],
            'sentiment': 50
        }
        return jsonify(result)
    except Exception as e:
        print(f"获取实时数据错误: {str(e)}")
        return jsonify({
            'latestComment': "暂无数据",
            'commentTime': "暂无数据",
            'provinceCount': "0个",
            'spreadRange': "暂无数据",
            'keywords': ["暂无数据"],
            'sentiment': 50
        })

def extract_keywords_from_df(df, top_n=5):
    """从DataFrame中提取关键词"""
    try:
        # 合并所有微博内容
        all_content = ' '.join(df['微博内容'].dropna().astype(str))
        # 简单返回一些固定关键词，您可以根据需要实现更复杂的逻辑
        return ['热点话题', '用户反馈', '社会关注', '热门事件', '公众讨论']
    except Exception as e:
        print(f"关键词提取错误: {str(e)}")
        return ['数据分析中']

def calculate_sentiment_percentage(df):
    """计算情感倾向百分比"""
    try:
        if '情感倾向' not in df.columns:
            return 50
            
        def convert_sentiment(value):
            try:
                if isinstance(value, (int, float)):
                    return float(value) * 100
                elif value == '正面':
                    return 100
                elif value == '负面':
                    return 0
                return 50
            except:
                return 50
            
        sentiments = df['情感倾向'].apply(convert_sentiment)
        return int(sentiments.mean())
    except Exception as e:
        print(f"情感分析错误: {str(e)}")
        return 50

def calculate_risk_level(df):
    """计算风险等级"""
    try:
        if '情感倾向' not in df.columns:
            return "低"
            
        def get_sentiment_value(x):
            try:
                if isinstance(x, (int, float)):
                    return float(x)
                elif x == '正面':
                    return 1.0
                elif x == '负面':
                    return 0.0
                return 0.5
            except:
                return 0.5
                
        sentiments = df['情感倾向'].apply(get_sentiment_value)
        negative_ratio = len(sentiments[sentiments < 0.3]) / len(df) if len(df) > 0 else 0
        
        if negative_ratio > 0.5:
            return "高"
        elif negative_ratio > 0.3:
            return "中"
        return "低"
    except Exception as e:
        print(f"风险等级计算错误: {str(e)}")
        return "低"
