import atexit
from datetime import datetime, timedelta
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
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

pb = Blueprint('page',__name__,url_prefix='/page',template_folder='templates')
ready_path = get_persistent_file_path('all','any')
# 全局字典来存储每个任务的状态
task_status = {}

def run_wordcloud_task(csv_path, task_id):
    try:
        get_wordcloud_csv(csv_path)
        task_status[task_id] = "completed"
        print(f"词云生成任务完成: {task_id}")
    except Exception as e:
        task_status[task_id] = f"error: {str(e)}"
        print(f"词云生成任务失败: {task_id}, 错误: {str(e)}")
    finally:
        try:
            if scheduler.get_job(task_id):
                scheduler.remove_job(task_id)
        except Exception as e:
            print(f"移除任务时出错: {str(e)}")

def convert_sentiment_to_text(score):
    """将情感分数转换为文字描述"""
    try:
        score = float(score)
        if score >= 0.7:
            return "正面"
        elif score <= 0.3:
            return "负面"
        else:
            return "中性"
    except (ValueError, TypeError):
        return "未知"

def get_data_file():
    """获取数据文件路径并确保目录存在"""
    try:
        # 优先使用ready_path
        if os.path.exists(ready_path):
            print(f"使用默认数据文件：{ready_path}")
            return ready_path
            
        # 确保目录存在
        data_dir = os.path.dirname(ready_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"创建数据目录：{data_dir}")
            
        # 创建空文件
        if not os.path.exists(ready_path):
            with open(ready_path, 'w', encoding='utf-8') as f:
                f.write("微博作者,微博内容,发布时间,转发数,评论数,点赞数,省份,url\n")
            print(f"创建空数据文件：{ready_path}")
            
        return ready_path
    except Exception as e:
        print(f"获取数据文件出错: {str(e)}")
        return ready_path

@pb.route('/')
@pb.route('/home')
def home():
    try:
        # 获取基础统计数据
        unique_user_count, total_heat_value, unique_ip_count, row_count = fenxi()
    except Exception as e:
        print(f"获取基础统计数据失败: {str(e)}")
        unique_user_count = total_heat_value = unique_ip_count = row_count = 0

    try:
        # 获取爬取结果数据
        if os.path.exists(ready_path):
            print(f"正在读取CSV文件: {ready_path}")
            df = pd.read_csv(ready_path, encoding='utf-8')
            print(f"成功读取CSV文件，数据行数: {len(df)}")
            print(f"列名: {df.columns.tolist()}")
            
            # 准备展示数据
            infos2_data = []
            for _, row in df.iterrows():
                try:
                    # 确保数值类型的字段为整数
                    shares = pd.to_numeric(row['转发数'], errors='coerce')
                    comments = pd.to_numeric(row['评论数'], errors='coerce')
                    likes = pd.to_numeric(row['点赞数'], errors='coerce')
                    
                    info = {
                        'author': str(row['微博作者']).strip() if pd.notna(row['微博作者']) else "未知作者",
                        'content': str(row['微博内容']).strip() if pd.notna(row['微博内容']) else "无内容",
                        'time': str(row['发布时间']).strip() if pd.notna(row['发布时间']) else "未知时间",
                        'shares': int(shares) if pd.notna(shares) else 0,
                        'comments': int(comments) if pd.notna(comments) else 0,
                        'likes': int(likes) if pd.notna(likes) else 0,
                        'url': str(row['url']).strip() if pd.notna(row['url']) else "#",
                        'profile_url': "#"
                    }
                    infos2_data.append(info)
                    if len(infos2_data) >= 100:  # 限制显示数量
                        break
                except Exception as e:
                    print(f"处理行数据时出错: {str(e)}")
                    continue
            print(f"成功处理数据，共{len(infos2_data)}条记录")
            print(f"数据示例: {infos2_data[0] if infos2_data else '无数据'}")
        else:
            print(f"CSV文件不存在: {ready_path}")
            infos2_data = []
    except Exception as e:
        print(f"获取爬取结果数据失败: {str(e)}")
        print(f"错误详情: {str(e.__class__.__name__)}")
        infos2_data = []

    try:
        # 获取每日热点数据
        current_date = datetime.now().strftime('%Y%m%d')
        csv_file_name = f'{current_date}_pengpai.csv'
        target_dir = os.path.join(root_dir, 'static', 'content')
        images_dir = os.path.join(target_dir, csv_file_name)
        
        if os.path.exists(images_dir):
            print(f"文件 {csv_file_name} 存在，正在读取...")
            daily_hotspots = []
            with open(images_dir, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    daily_hotspots.append({
                        'title': row['标题'],
                        'cover_image': row['封面链接'],
                        'source': row['发文者'],
                        'link': row['链接'],
                        'read_link': row['down_link']
                    })
        else:
            print("热点数据文件不存在，尝试获取新数据...")
            daily_hotspots = get_pengpai_list()
    except Exception as e:
        print(f"获取每日热点数据失败: {str(e)}")
        daily_hotspots = []

    return render_template('index.html',
                         row_count=row_count,
                         unique_user_count=unique_user_count,
                         total_heat_value=total_heat_value,
                         unique_ip_count=unique_ip_count,
                         infos2_data=infos2_data,
                         daily_hotspots=daily_hotspots
                         )

@pb.route('/case_study')
def case_study():
    try:
        return render_template('case_study.html')
    except Exception as e:
        print(f"加载案例页面时发生错误: {str(e)}")
        return f"加载案例页面时发生错误: {str(e)}", 500

@pb.route('/settle')
def settle():
    try:
        return render_template('settle.html')
    except Exception as e:
        print(f"加载页面时发生错误: {str(e)}")
        return f"加载页面时发生错误: {str(e)}", 500

@pb.route('/case_manage')
def case_manage():
    return render_template('case_manage.html')

@pb.route('/setting_spider',methods=['GET','POST'])
def setting_spider():
    if request.method == "GET":
        try:
            # 获取历史记录
            history_records = []
            if os.path.exists('memory.csv'):
                with open('memory.csv', 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        try:
                            # 处理平台字段，将字符串转换为列表
                            platforms = eval(row['平台']) if isinstance(row['平台'], str) else row['平台']
                            history_records.append({
                                'timestamp': row['时间'],
                                'platform': ', '.join(platforms),
                                'keyword': row['关键词'],
                                'start_date': row['开始时间'],
                                'end_date': row['截止时间'],
                                'precision': row['精度']
                            })
                        except Exception as e:
                            print(f"处理历史记录行时出错: {str(e)}")
                            continue
        except Exception as e:
            print(f"读取历史记录时出错: {str(e)}")
            history_records = []

        try:
            # 获取现有数据（如果有）
            if os.path.exists(ready_path):
                df = pd.read_csv(ready_path, encoding='utf-8')
                infos2 = []
                for _, row in df.iterrows():
                    try:
                        # 处理情感倾向
                        sentiment = row.get('情感倾向', 0.5)
                        sentiment_text = convert_sentiment_to_text(sentiment)
                            
                        info = {
                            '用户名': str(row['微博作者']).strip() if pd.notna(row['微博作者']) else "未知作者",
                            '内容': str(row['微博内容']).strip() if pd.notna(row['微博内容']) else "无内容",
                            'sentiment_result': sentiment_text,
                            '发布时间': str(row['发布时间']).strip() if pd.notna(row['发布时间']) else "未知时间",
                            '分享数': int(row['转发数']) if pd.notna(row['转发数']) else 0,
                            '评论数': int(row['评论数']) if pd.notna(row['评论数']) else 0,
                            '点赞数': int(row['点赞数']) if pd.notna(row['点赞数']) else 0
                        }
                        infos2.append(info)
                    except Exception as e:
                        print(f"处理数据行时出错: {str(e)}")
                        continue
            else:
                infos2 = []
        except Exception as e:
            print(f"读取数据文件时出错: {str(e)}")
            infos2 = []

        return render_template('spider_setting.html',
                            infos2=infos2,
                            history_records=history_records)

    elif request.method == "POST":
        try:
            # 获取表单数据
            keyword = request.form.get('keyword')
            platforms = request.form.getlist('platforms[]')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            precision = request.form.get('precision')

            if not keyword or not platforms:
                return jsonify({
                    'status': 'error',
                    'message': '关键词和平台是必填项'
                }), 400

            # 平台映射
            mapping_dict = {
                'douyin': '抖音',
                'weibo': '微博',
                'bilibili': '哔哩哔哩'
            }
            platforms = [mapping_dict.get(item, item) for item in platforms]

            # 精度映射
            mapping2_dict = {
                'low': '低',
                'medium': '中',
                'high': '高'
            }
            precision = mapping2_dict.get(precision, precision)

            # 保存历史记录
            try:
                memory_headers = ["时间", "平台", "关键词", "开始时间", "截止时间", "精度"]
                file_exists = os.path.exists('memory.csv')
                
                with open('memory.csv', mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    if not file_exists:
                        writer.writerow(memory_headers)
                    
                    now = datetime.now()
                    formatted_now = now.strftime('%Y-%m-%d %H:%M')
                    writer.writerow([formatted_now, platforms, keyword, start_date, end_date, precision])
            except Exception as e:
                print(f"保存历史记录时出错: {str(e)}")

            # 执行爬虫任务
            try:
                infos2, share_num, comment_num, like_num, sentiment_counts = dynamic_spider_task(
                    keyword, platforms, start_date, end_date, precision)
                print(f"动态爬虫任务已启动: {keyword}")

                # 生成任务ID并添加词云生成任务
                random_six_digit_number = random.randint(100000, 999999)
                task_id = f"wordcloud_{keyword}_{random_six_digit_number}"
                csv_path = f"{keyword}.csv"

                # 添加词云生成任务
                scheduler.add_job(
                    run_wordcloud_task,
                    args=[csv_path, task_id],
                    id=task_id,
                    trigger='date',
                    run_date=datetime.now() + timedelta(seconds=5)
                )
                
                task_status[task_id] = "running"

                # 转换情感分析结果为文字描述
                sentiment_text_counts = {}
                for score, count in sentiment_counts.items():
                    sentiment_text = convert_sentiment_to_text(score)
                    sentiment_text_counts[sentiment_text] = sentiment_text_counts.get(sentiment_text, 0) + count

                # 准备返回数据
                response_data = {
                    'status': 'success',
                    'message': '数据爬取成功',
                    'task_id': task_id,
                    'data': {
                        'infos2': infos2,
                        'positive_count': sentiment_text_counts.get('正面', 0),
                        'negative_count': sentiment_text_counts.get('负面', 0),
                        'neutral_count': sentiment_text_counts.get('中性', 0)
                    }
                }

                # 更新数据文件
                if os.path.exists(ready_path):
                    df = pd.read_csv(ready_path, encoding='utf-8')
                    new_data = pd.DataFrame(infos2)
                    df = pd.concat([df, new_data], ignore_index=True)
                    df.to_csv(ready_path, index=False, encoding='utf-8')

                return jsonify(response_data)

            except Exception as e:
                print(f"执行爬虫任务时出错: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'爬虫任务执行失败: {str(e)}'
                }), 500

        except Exception as e:
            print(f"处理POST请求时出错: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'请求处理失败: {str(e)}'
            }), 500

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
        
        # 检查必要的列是否存在
        required_columns = ['情感倾向', '省份']  # 性别列不是必需的
        missing_columns = [col for col in required_columns if col not in df_sentiment.columns]
        if missing_columns:
            print(f"警告：缺少必要的列：{missing_columns}")
            raise ValueError(f"缺少必要的列：{missing_columns}")

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
            except (ValueError, TypeError):
                return '中性'  # 如果无法转换为浮点数，默认中性

        # 处理性别数据
        def normalize_gender(value):
            if pd.isna(value):
                return '未知'
            value = str(value).lower()
            if value in ['m', '男', 'male', '1']:
                return '男'
            elif value in ['f', '女', 'female', '2']:
                return '女'
            else:
                return '未知'

        df_sentiment['情感倾向'] = df_sentiment['情感倾向'].apply(classify_sentiment)
        
        # 如果存在性别列，则进行处理，否则创建默认值
        if '性别' in df_sentiment.columns:
            df_sentiment['性别'] = df_sentiment['性别'].apply(normalize_gender)
            gender_counts = df_sentiment['性别'].value_counts()
            gender_data = {
                '男': int(gender_counts.get('男', 0)),
                '女': int(gender_counts.get('女', 0))
            }
        else:
            print("警告：未找到性别列，使用默认值")
            gender_data = {'男': 0, '女': 0}

        # 统计情感倾向分布
        sentiment_counts = df_sentiment['情感倾向'].value_counts()
        sentiment_data = {
            '正面': int(sentiment_counts.get('正面', 0)),
            '负面': int(sentiment_counts.get('负面', 0)),
            '中性': int(sentiment_counts.get('中性', 0))
        }

        # 对省份进行计数
        province_counts = df_sentiment['省份'].value_counts().to_dict()
        heatmap_data = [
            {
                "name": province,
                "value": int(value)
            }
            for province, value in province_counts.items()
            if province and province != 'nan'  # 过滤掉空值和nan
        ]

        return jsonify({
            'heatmapData': heatmap_data,
            'sentimentData': sentiment_data,
            'genderData': gender_data
        })

    except Exception as e:
        print(f"Error in get_chart_data: {str(e)}")
        print(traceback.format_exc())  # 打印完整的错误堆栈
        # 返回默认数据
        return jsonify({
            'heatmapData': [],
            'sentimentData': {'正面': 0, '负面': 0, '中性': 0},
            'genderData': {'男': 0, '女': 0}
        })

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
    try:
        df = pd.read_csv(ready_path, encoding='utf-8')
        # 使用统一的列名
        required_columns = ['用户名', '内容', 'url']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"警告：缺少必要的列：{missing_columns}")
            return json.dumps([], ensure_ascii=False, indent=2)
            
        json_data = []
        for index, row in df.iterrows():
            # 检查并处理NaN值
            author = row['用户名'] if pd.notna(row['用户名']) else "未知作者"
            content = row['内容'] if pd.notna(row['内容']) else "无内容"
            url = row['url'] if pd.notna(row['url']) else "#"
            
            json_data.append({
                "author": author,
                "content": content,
                "Link": url,
                "authorUrl": url  # 使用相同的URL作为作者链接
            })
        # 使用ensure_ascii=False来正确处理中文字符
        return json.dumps(json_data, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error in get_realtime_monitoring: {str(e)}")
        print(traceback.format_exc())
        return json.dumps([], ensure_ascii=False, indent=2)



@pb.route('/stop_spider_task', methods=['POST'])
def stop_spider_task():
    """停止所有爬虫任务"""
    try:
        jobs = scheduler.get_jobs()
        for job in jobs:
            scheduler.remove_job(job.id)
        task_status.clear()
        
        return jsonify({
            'status': 'success',
            'message': '所有任务已停止'
        })
    except Exception as e:
        print(f"停止任务时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'停止任务失败: {str(e)}'
        }), 500


@pb.route('/api/status')
def get_status():
    """获取当前任务状态"""
    try:
        jobs = scheduler.get_jobs()
        if not jobs:
            return jsonify({
                'status': 'idle',
                'message': '系统就绪 - 欢迎使用爬虫系统'
            })

        # 获取所有爬虫任务（以spider_job_开头的任务）
        spider_jobs = [job for job in jobs if job.id.startswith('spider_job_')]
        if spider_jobs:
            next_job = spider_jobs[0]  # 获取最近的爬虫任务
            keyword = next_job.id.replace('spider_job_', '')
            next_run_time = next_job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'status': 'scheduled',
                'message': f'下一次任务将于 {next_run_time} 执行，关键词：{keyword}'
            })

        # 检查词云任务
        wordcloud_jobs = [job for job in jobs if job.id.startswith('wordcloud_')]
        if wordcloud_jobs:
            task_id = wordcloud_jobs[0].id
            current_status = task_status.get(task_id, 'running')

            if current_status == 'completed':
                return jsonify({
                    'status': 'success',
                    'message': '任务已完成'
                })
            elif current_status.startswith('error'):
                return jsonify({
                    'status': 'error',
                    'message': current_status
                })
            else:
                return jsonify({
                    'status': 'working',
                    'message': '正在处理数据...'
                })

        return jsonify({
            'status': 'idle',
            'message': '系统就绪 - 欢迎使用爬虫系统'
        })

    except Exception as e:
        print(f"获取状态时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取状态失败: {str(e)}'
        }), 500

@pb.route('/api/stats')
def get_stats():
    """获取实时统计数据"""
    try:
        data_file = get_data_file()
        print(f"正在读取数据文件：{data_file}")
        
        if not os.path.exists(data_file):
            print(f"数据文件不存在：{data_file}")
            return jsonify({
                'todayMonitor': 0,
                'totalComments': 0,
                'heatIndex': 0,
                'riskLevel': '低'
            })

        df = pd.read_csv(data_file, encoding='utf-8')
        print(f"成功读取数据，行数：{len(df)}")

        # 计算今日数据
        df['发布时间'] = pd.to_datetime(df['发布时间'], errors='coerce')
        today = datetime.now().strftime('%Y-%m-%d')
        today_data = df[df['发布时间'].dt.strftime('%Y-%m-%d') == today]

        # 计算评论数和热度
        total_comments = df['评论数'].sum() if '评论数' in df.columns else 0
        heat_index = int((df['转发数'].sum() * 0.4 + 
                         df['评论数'].sum() * 0.3 + 
                         df['点赞数'].sum() * 0.3) / 100)

        return jsonify({
            'todayMonitor': len(today_data),
            'totalComments': int(total_comments),
            'heatIndex': heat_index,
            'riskLevel': '低'
        })

    except Exception as e:
        print(f"获取统计数据出错: {str(e)}")
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
        data_file = ready_path
        print(f"数据文件路径: {data_file}")
        
        if not os.path.exists(data_file):
            print(f"数据文件不存在: {data_file}")
            return jsonify({
                'latestComment': "暂无数据",
                'commentTime': "暂无数据",
                'provinceCount': "0个",
                'spreadRange': "暂无数据",
                'keywords': ["暂无数据"],
                'sentiment': 50
            })

        # 尝试不同编码读取文件
        for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
            try:
                df = pd.read_csv(data_file, encoding=encoding)
                print(f"使用 {encoding} 编码成功读取文件")
                break
            except Exception as e:
                print(f"使用 {encoding} 编码读取失败: {str(e)}")
                continue
        else:
            print("所有编码尝试均失败")
            return jsonify({
                'latestComment': "数据读取失败",
                'commentTime': "暂无数据",
                'provinceCount': "0个",
                'spreadRange': "暂无数据",
                'keywords': ["数据读取失败"],
                'sentiment': 50
            })

        print(f"成功读取数据文件，行数：{len(df)}")
        print(f"列名：{df.columns.tolist()}")

        if len(df) == 0:
            return jsonify({
                'latestComment': "暂无数据",
                'commentTime': "暂无数据",
                'provinceCount': "0个",
                'spreadRange': "暂无数据",
                'keywords': ["暂无数据"],
                'sentiment': 50
            })

        # 获取最新评论
        latest_row = df.iloc[-1]
        
        # 定义可能的列名映射
        column_mappings = {
            'content': ['微博内容', '内容', 'content', '评论内容', '文本内容', 'text'],
            'time': ['发布时间', '时间', 'time', '评论时间', '创建时间', 'created_at'],
            'author': ['微博作者', '作者', 'author', '用户名', 'username'],
            'province': ['省份', '地区', 'province', 'location', '位置'],
            'shares': ['转发数', '分享数', 'shares', 'repost_count'],
            'comments': ['评论数', 'comments', 'comment_count'],
            'likes': ['点赞数', '赞数', 'likes', 'like_count']
        }

        # 获取实际的列名
        actual_columns = {}
        for key, possible_names in column_mappings.items():
            for name in possible_names:
                if name in df.columns:
                    actual_columns[key] = name
                    break
            if key not in actual_columns:
                print(f"未找到{key}对应的列名")
                actual_columns[key] = None

        # 获取内容和时间
        latest_comment = str(latest_row[actual_columns['content']]) if actual_columns['content'] else "暂无数据"
        comment_time = str(latest_row[actual_columns['time']]) if actual_columns['time'] else "暂无数据"

        # 计算省份数据
        province_count = df[actual_columns['province']].nunique() if actual_columns['province'] else 0
        spread_range = "全国性传播" if province_count > 20 else "区域性传播" if province_count > 10 else "局部传播"

        # 提取关键词（可以根据实际需求实现）
        keywords = extract_keywords_from_df(df) if len(df) > 0 else ["暂无数据"]

        # 计算情感值
        sentiment = calculate_sentiment_percentage(df)

        response_data = {
            'latestComment': latest_comment[:200] + '...' if len(latest_comment) > 200 else latest_comment,
            'commentTime': comment_time,
            'provinceCount': f"{province_count}个",
            'spreadRange': spread_range,
            'keywords': keywords,
            'sentiment': sentiment
        }
        
        print(f"返回数据：{json.dumps(response_data, ensure_ascii=False)}")
        return jsonify(response_data)

    except Exception as e:
        print(f"获取实时数据出错: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'latestComment': "数据获取失败",
            'commentTime': "暂无数据",
            'provinceCount': "0个",
            'spreadRange': "暂无数据",
            'keywords': ["数据获取失败"],
            'sentiment': 50
        })

def extract_keywords_from_df(df, top_n=5):
    """从DataFrame中提取关键词"""
    try:
        # 合并所有内容
        all_content = ' '.join(df['内容'].dropna().astype(str))
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

# API路由
@pb.route('/api/cases', methods=['GET'])
def get_cases():
    try:
        cases = []
        # 读取案例数据
        with open('views/page/data/cases.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            cases = list(reader)
            
        # 对每个案例添加时间线、分析和建议数据
        for case in cases:
            # 读取时间线数据
            timelines = []
            with open('views/page/data/timelines.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['case_id'] == case['id']:
                        timelines.append({
                            'phase': row['phase'],
                            'date': row['date'],
                            'content': row['content']
                        })
            case['timeline'] = timelines
            
            # 读取分析数据
            analysis = []
            with open('views/page/data/analysis.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['case_id'] == case['id']:
                        analysis.append({
                            'title': row['title'],
                            'content': row['content']
                        })
            case['analysis'] = analysis
            
            # 读取建议数据
            suggestions = []
            with open('views/page/data/suggestions.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['case_id'] == case['id']:
                        suggestions.append({
                            'title': row['title'],
                            'content': row['content']
                        })
            case['suggestions'] = suggestions
            
        return jsonify(cases)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pb.route('/api/cases/<int:case_id>', methods=['GET'])
def get_case(case_id):
    cases = load_cases()
    case = next((case for case in cases if case['id'] == case_id), None)
    if case is None:
        return jsonify({'error': '案例不存在'}), 404
    return jsonify(case)

@pb.route('/api/get_latest_data')
def get_latest_data():
    """获取最新数据的API端点"""
    try:
        if os.path.exists(ready_path):
            df = pd.read_csv(ready_path, encoding='utf-8')
            infos2 = []
            for _, row in df.iterrows():
                try:
                    # 处理情感倾向
                    sentiment = row.get('情感倾向', 0.5)
                    sentiment_text = convert_sentiment_to_text(sentiment)
                        
                    info = {
                        '用户名': str(row['微博作者']).strip() if pd.notna(row['微博作者']) else "未知作者",
                        '内容': str(row['微博内容']).strip() if pd.notna(row['微博内容']) else "无内容",
                        'sentiment_result': sentiment_text,
                        '发布时间': str(row['发布时间']).strip() if pd.notna(row['发布时间']) else "未知时间",
                        '分享数': int(row['转发数']) if pd.notna(row['转发数']) else 0,
                        '评论数': int(row['评论数']) if pd.notna(row['评论数']) else 0,
                        '点赞数': int(row['点赞数']) if pd.notna(row['点赞数']) else 0
                    }
                    infos2.append(info)
                except Exception as e:
                    print(f"处理数据行时出错: {str(e)}")
                    continue

            return jsonify({
                'status': 'success',
                'data': infos2
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '数据文件不存在'
            }), 404
    except Exception as e:
        print(f"获取数据时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取数据失败: {str(e)}'
        }), 500