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
import jieba
import json
import time
import uuid
from utils.report_generator import ReportGenerator
from model.ai_assistant import get_chat_response, verify_access_password, save_chat_history, load_chat_history
import os
import traceback  # 添加这个用于详细错误追踪
from utils.ai_assistant_logger import log_user_activity, log_system_event, get_client_ip
from config.settings import ZHIPUAI_API_KEY, MODEL_CONFIG, REPORT_CONFIG
from utils.auth_decorator import login_required

# 全局变量
scheduler = BackgroundScheduler()
# 不在模块导入时启动调度器，而是在需要时启动
_scheduler_started = False

def ensure_scheduler_started():
    """确保调度器已启动"""
    global _scheduler_started
    if not _scheduler_started:
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
        _scheduler_started = True
        print("调度器已启动")

def load_home_data_cached():
    """加载主页数据（带缓存）"""
    global _home_data_cache
    import time

    current_time = time.time()

    # 检查缓存是否有效
    cache_age = current_time - _home_data_cache['timestamp']
    print(f"缓存检查: 数据存在={_home_data_cache['data'] is not None}, 缓存年龄={cache_age:.1f}秒, 缓存期限={_home_data_cache['cache_duration']}秒")

    if (_home_data_cache['data'] is not None and
        cache_age < _home_data_cache['cache_duration']):
        print("✅ 使用缓存的主页数据")
        return _home_data_cache['data']

    print("🔄 重新加载主页数据...")

    # 加载基础统计数据
    try:
        unique_user_count, total_heat_value, unique_ip_count, row_count = fenxi()
    except Exception as e:
        print(f"获取基础统计数据失败: {str(e)}")
        unique_user_count = total_heat_value = unique_ip_count = row_count = 0

    # 快速加载微博数据（只读取前20条）
    infos2_data = []
    try:
        if os.path.exists(ready_path):
            file_size = os.path.getsize(ready_path) / (1024 * 1024)  # MB
            print(f"快速读取CSV文件: {ready_path} (大小: {file_size:.2f}MB)")

            # 只读取前20行以提高速度
            df = pd.read_csv(ready_path, encoding='utf-8', nrows=20)
            print(f"快速读取完成，数据行数: {len(df)}")

            for i in range(min(20, len(df))):
                try:
                    row = df.iloc[i]
                    shares = pd.to_numeric(row['转发数'], errors='coerce')
                    comments = pd.to_numeric(row['评论数'], errors='coerce')
                    likes = pd.to_numeric(row['点赞数'], errors='coerce')

                    info = {
                        'author': str(row['微博作者']).strip() if pd.notna(row['微博作者']) else "未知作者",
                        'content': str(row['微博内容']).strip()[:150] if pd.notna(row['微博内容']) else "无内容",  # 进一步限制内容长度
                        'time': str(row['发布时间']).strip() if pd.notna(row['发布时间']) else "未知时间",
                        'shares': int(shares) if pd.notna(shares) else 0,
                        'comments': int(comments) if pd.notna(comments) else 0,
                        'likes': int(likes) if pd.notna(likes) else 0,
                        'url': str(row['url']).strip() if pd.notna(row['url']) else "#",
                        'profile_url': "#"
                    }
                    infos2_data.append(info)
                except Exception as e:
                    print(f"处理行数据时出错: {str(e)}")
                    continue
        else:
            print(f"CSV文件不存在: {ready_path}")
    except Exception as e:
        print(f"快速加载数据失败: {str(e)}")
        infos2_data = []

    # 加载每日热点数据（恢复完整功能）
    daily_hotspots = []
    try:
        current_date = datetime.now().strftime('%Y%m%d')
        csv_file_name = f'{current_date}_pengpai.csv'
        target_dir = os.path.join(root_dir, 'static', 'content')
        images_dir = os.path.join(target_dir, csv_file_name)

        print(f"查找热点文件: {images_dir}")

        if os.path.exists(images_dir):
            print(f"✅ 找到热点文件: {csv_file_name}")
            with open(images_dir, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    if count >= 8:  # 加载8条热点数据
                        break
                    try:
                        hotspot = {
                            'title': row.get('标题', '无标题')[:100],  # 限制标题长度
                            'cover_image': row.get('封面链接', ''),
                            'link': row.get('链接', '#'),  # 使用link而不是url
                            'source': row.get('发文者', '未知来源'),
                            'read_link': row.get('down_link', '#')
                        }
                        daily_hotspots.append(hotspot)
                        count += 1
                    except Exception as e:
                        print(f"处理热点数据行时出错: {str(e)}")
                        continue
            print(f"✅ 成功加载 {len(daily_hotspots)} 条热点数据")
        else:
            print(f"⚠️ 热点文件不存在: {csv_file_name}")
            print("尝试获取新的热点数据...")
            # 如果文件不存在，尝试获取新数据
            try:
                from spiders.pengpai import get_pengpai_list
                daily_hotspots = get_pengpai_list()
                print(f"✅ 从网络获取到 {len(daily_hotspots)} 条热点数据")
            except Exception as e:
                print(f"❌ 获取网络热点数据失败: {str(e)}")
                daily_hotspots = []
    except Exception as e:
        print(f"❌ 加载热点数据失败: {str(e)}")
        daily_hotspots = []

    # 缓存数据
    data = {
        'unique_user_count': unique_user_count,
        'total_heat_value': total_heat_value,
        'unique_ip_count': unique_ip_count,
        'row_count': row_count,
        'infos2_data': infos2_data,
        'daily_hotspots': daily_hotspots
    }

    _home_data_cache['data'] = data
    _home_data_cache['timestamp'] = current_time

    print(f"📊 主页数据加载完成，已缓存")
    print(f"   - 微博数据: {len(infos2_data)}条")
    print(f"   - 热点数据: {len(daily_hotspots)}条")
    if daily_hotspots:
        print(f"   - 热点示例: {daily_hotspots[0]['title'][:50]}...")

    return data
# 获取当前文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

pb = Blueprint('page',__name__,url_prefix='/page',template_folder='templates')
ready_path = get_persistent_file_path('all','any')
# 全局字典来存储每个任务的状态
task_status = {}
# 初始化realtime_csv_path全局变量
realtime_csv_path = ready_path  # 设置默认值为ready_path

# 添加数据缓存
_home_data_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 300  # 5分钟缓存
}

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
            ensure_scheduler_started()  # 确保调度器已启动
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
@login_required
def home():
    """主页 - 使用缓存优化加载速度"""
    try:
        # 使用缓存数据快速加载
        data = load_home_data_cached()

        unique_user_count = data['unique_user_count']
        total_heat_value = data['total_heat_value']
        unique_ip_count = data['unique_ip_count']
        row_count = data['row_count']
        infos2_data = data['infos2_data']
        daily_hotspots = data['daily_hotspots']

        # 调试信息
        print(f"🏠 主页数据准备完成:")
        print(f"   - 微博数据: {len(infos2_data)}条")
        print(f"   - 热点数据: {len(daily_hotspots)}条")

    except Exception as e:
        print(f"❌ 加载主页数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 提供默认值
        unique_user_count = total_heat_value = unique_ip_count = row_count = 0
        infos2_data = []
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
@login_required
def case_study():
    try:
        return render_template('case_study.html')
    except Exception as e:
        print(f"加载案例页面时发生错误: {str(e)}")
        return f"加载案例页面时发生错误: {str(e)}", 500

@pb.route('/settle')
@login_required
def settle():
    try:
        return render_template('settle.html')
    except Exception as e:
        print(f"加载页面时发生错误: {str(e)}")
        return f"加载页面时发生错误: {str(e)}", 500

@pb.route('/case_manage')
@login_required
def case_manage():
    return render_template('case_manage.html')

@pb.route('/setting_spider',methods=['GET','POST'])
@login_required
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
                # 更新任务状态为正在执行
                spider_task_id = f"spider_{keyword}_{random.randint(100000, 999999)}"
                task_status[spider_task_id] = f"正在爬取数据: {keyword}"

                infos2, share_num, comment_num, like_num, sentiment_counts = dynamic_spider_task(
                    keyword, platforms, start_date, end_date, precision)
                print(f"动态爬虫任务已启动: {keyword}")

                # 更新任务状态为完成
                task_status[spider_task_id] = "completed"

                # 生成任务ID并添加词云生成任务
                random_six_digit_number = random.randint(100000, 999999)
                task_id = f"wordcloud_{keyword}_{random_six_digit_number}"
                try:
                    for item in platforms:
                        if item == '微博':
                            csv_path = get_temp_file_path('weibo',keyword)
                            break
                        else:
                            csv_path = get_temp_file_path('douyin',keyword)
                except:
                    csv_path = get_temp_file_path('weibo',keyword)
                    print(f'平台读取有误，采用默认路径{csv_path}')
                # 添加词云生成任务
                ensure_scheduler_started()  # 确保调度器已启动
                scheduler.add_job(
                    run_wordcloud_task,
                    args=[csv_path, task_id],
                    id=task_id,
                    trigger='date',
                    run_date=datetime.now() + timedelta(seconds=5)
                )
                global realtime_csv_path
                realtime_csv_path = csv_path
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
@login_required
def tableData():
    users = session.get('username')
    return render_template('bigdata.html',
                           user_name=users,
                           )

@pb.route('/q_a')
@login_required
def q_a():
    users = session.get('username')
    return render_template('question_answer.html',
                           user_name=users,
                           )




@pb.route('/table')
@login_required
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
@login_required
def get_chart_data():
    try:
        df_sentiment = pd.read_csv(realtime_csv_path)
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
@login_required
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
@login_required
def get_realtime_monitoring():
    try:
        df = pd.read_csv(realtime_csv_path, encoding='utf-8')

        # 定义可能的列名映射
        column_mappings = {
            'author': ['用户名', '微博作者', '作者', '发布者', 'author'],
            'content': ['内容', '微博内容', '视频描述', '文本内容', '评论内容', 'content', 'text'],
            'url': ['url', 'URL', '链接', 'link', '视频链接']
        }

        # 查找实际使用的列名
        actual_columns = {}
        for key, possible_names in column_mappings.items():
            found = False
            for name in possible_names:
                if name in df.columns:
                    actual_columns[key] = name
                    found = True
                    break
            if not found:
                print(f"警告：未找到{key}对应的列名")
                actual_columns[key] = None

        # 确保必要的列存在
        if not all(actual_columns.values()):
            missing_columns = [k for k, v in actual_columns.items() if v is None]
            print(f"警告：缺少必要的列：{missing_columns}")
            return json.dumps([], ensure_ascii=False, indent=2)

        json_data = []
        for index, row in df.iterrows():
            try:
                # 使用找到的实际列名获取数据，并进行空值处理
                author = str(row[actual_columns['author']]) if pd.notna(row[actual_columns['author']]) else "未知作者"
                content = str(row[actual_columns['content']]) if pd.notna(row[actual_columns['content']]) else "无内容"
                url = str(row[actual_columns['url']]) if pd.notna(row.get(actual_columns['url'])) else "#"

                json_data.append({
                    "author": author.strip(),
                    "content": content.strip(),
                    "Link": url.strip(),
                    "authorUrl": url.strip()  # 使用相同的URL作为作者链接
                })

            except Exception as e:
                print(f"处理行 {index} 时出错: {str(e)}")
                continue

        # 使用ensure_ascii=False来正确处理中文字符
        return json.dumps(json_data, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Error in get_realtime_monitoring: {str(e)}")
        print(traceback.format_exc())
        return json.dumps([], ensure_ascii=False, indent=2)

@pb.route('/stop_spider_task', methods=['POST'])
@login_required
def stop_spider_task():
    """停止所有爬虫任务"""
    try:
        ensure_scheduler_started()  # 确保调度器已启动
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


@pb.route('/api/cache/clear', methods=['POST'])
@login_required
def clear_home_cache():
    """清理主页数据缓存"""
    global _home_data_cache
    _home_data_cache['data'] = None
    _home_data_cache['timestamp'] = 0
    return jsonify({'message': '主页缓存已清理'})

@pb.route('/api/hotspots/debug')
def debug_hotspots():
    """调试热点数据API"""
    try:
        data = load_home_data_cached()
        hotspots = data.get('daily_hotspots', [])

        return jsonify({
            'hotspots_count': len(hotspots),
            'hotspots': hotspots[:3],  # 只返回前3条用于调试
            'cache_info': {
                'has_cache': _home_data_cache['data'] is not None,
                'cache_timestamp': _home_data_cache['timestamp']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pb.route('/api/status')
def get_status():
    """获取当前任务状态（无需登录，快速响应）"""
    try:
        # 首先检查全局任务状态
        if task_status:
            # 检查是否有正在运行的任务
            running_tasks = [task_id for task_id, status in task_status.items()
                           if status not in ['completed', 'error']]
            if running_tasks:
                return jsonify({
                    'status': 'working',
                    'message': f'正在执行任务: {", ".join(running_tasks[:2])}'
                })

        # 检查调度器状态
        if not _scheduler_started:
            return jsonify({
                'status': 'idle',
                'message': '系统就绪 - 欢迎使用爬虫系统'
            })

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
@login_required
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
@login_required
def generate_report():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400

        depth = data.get('depth', 'standard')

        if not os.path.exists(realtime_csv_path):
            return jsonify({'error': 'CSV文件不存在'}), 404

        generator = ReportGenerator(realtime_csv_path)

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
@login_required
def get_realtime_data():
    """获取实时舆情数据"""
    try:
        data_file = realtime_csv_path
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

        # 获取内容和时间（过滤空值和NaN）
        if actual_columns['content']:
            # 过滤掉空值和NaN的内容
            valid_content_mask = df[actual_columns['content']].notna() & (df[actual_columns['content']].str.strip() != '')
            valid_content_df = df[valid_content_mask]

            if len(valid_content_df) > 0:
                latest_row = valid_content_df.iloc[-1]
                latest_comment = str(latest_row[actual_columns['content']]).strip()
            else:
                latest_comment = "暂无有效数据"
        else:
            latest_comment = "暂无数据"

        comment_time = str(latest_row[actual_columns['time']]) if actual_columns['time'] and 'latest_row' in locals() else "暂无数据"

        # 计算省份数据
        province_count = df[actual_columns['province']].nunique() if actual_columns['province'] else 0
        spread_range = "全国性传播" if province_count > 20 else "区域性传播" if province_count > 10 else "局部传播"

        # 提取关键词
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
    """从DataFrame中提取关键词

    Args:
        df: 包含文本数据的DataFrame
        top_n: 返回的关键词数量

    Returns:
        list: 前N个关键词
    """
    try:
        # 定义可能的内容列名
        content_columns = ['内容', '微博内容', '视频描述', 'content', 'text']
        content_col = None

        # 寻找包含内容的列
        for col in content_columns:
            if col in df.columns:
                content_col = col
                break

        if content_col is None:
            print("未找到包含内容的列")
            return ["暂无数据"]

        # 分词
        word_list = []
        for text in df[content_col]:
            if pd.notna(text):
                seg_list = jieba.cut(str(text))
                # 过滤掉长度小于等于1的词
                filtered_words = [word for word in seg_list if len(word) > 1]
                word_list.extend(filtered_words)

        # 统计词频
        word_counts = {}
        for word in word_list:
            word_counts[word] = word_counts.get(word, 0) + 1

        # 排序并返回前N个关键词
        sorted_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:top_n]]

    except Exception as e:
        print(f"关键词提取错误: {str(e)}")
        return ["数据处理中"]

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
    """计算风险等级

    基于多个维度计算风险等级：
    1. 情感倾向（负面情感占比）
    2. 传播速度（最近时间段的数据量）
    3. 互动程度（评论、转发、点赞总量）

    Returns:
        str: "高"/"中"/"低" 风险等级
    """
    try:
        if len(df) == 0:
            return "低"

        risk_score = 0

        # 1. 情感倾向分析
        if '情感倾向' in df.columns:
            def get_sentiment_value(x):
                try:
                    if isinstance(x, (int, float)):
                        return float(x)
                    elif isinstance(x, str):
                        if x == '正面':
                            return 1.0
                        elif x == '负面':
                            return 0.0
                        elif x == '中性':
                            return 0.5
                    return 0.5
                except:
                    return 0.5

            sentiments = df['情感倾向'].apply(get_sentiment_value)
            negative_ratio = len(sentiments[sentiments < 0.3]) / len(df)
            risk_score += negative_ratio * 40  # 情感倾向占40分

        # 2. 传播速度分析
        if '发布时间' in df.columns:
            try:
                df['发布时间'] = pd.to_datetime(df['发布时间'])
                recent_hours = 24
                recent_threshold = pd.Timestamp.now() - pd.Timedelta(hours=recent_hours)
                recent_count = len(df[df['发布时间'] >= recent_threshold])
                speed_score = min(recent_count / 100, 1.0) * 30  # 传播速度占30分
                risk_score += speed_score
            except:
                pass

        # 3. 互动程度分析
        interaction_columns = ['转发数', '评论数', '点赞数']
        if all(col in df.columns for col in interaction_columns):
            try:
                total_interactions = (
                    df['转发数'].astype(float).fillna(0) +
                    df['评论数'].astype(float).fillna(0) +
                    df['点赞数'].astype(float).fillna(0)
                ).sum()
                interaction_score = min(total_interactions / 10000, 1.0) * 30  # 互动程度占30分
                risk_score += interaction_score
            except:
                pass

        # 根据总分确定风险等级
        if risk_score >= 70:
            return "高"
        elif risk_score >= 40:
            return "中"
        return "低"

    except Exception as e:
        print(f"风险等级计算错误: {str(e)}")
        return "低"

# API路由
@pb.route('/api/cases', methods=['GET'])
@login_required
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
@login_required
def get_case(case_id):
    cases = load_cases()
    case = next((case for case in cases if case['id'] == case_id), None)
    if case is None:
        return jsonify({'error': '案例不存在'}), 404
    return jsonify(case)

@pb.route('/api/get_latest_data')
@login_required
def get_latest_data():
    """获取最新数据的API端点"""
    try:

        if os.path.exists(realtime_csv_path):
            df = pd.read_csv(realtime_csv_path, encoding='utf-8')
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

@pb.route('/manual')
@login_required
def manual():
    """网络舆情应对手册页面"""
    try:
        return render_template('manual.html')
    except Exception as e:
        print(f"渲染舆情应对手册页面失败: {str(e)}")
        return render_template('error.html', error_message="加载舆情应对手册页面失败")

@pb.route('/ai_assistant')
@login_required
def ai_assistant():
    """舆情分析AI助手页面"""
    try:
        # 创建存储目录（如果不存在）
        os.makedirs('data/chat_history', exist_ok=True)

        # 记录用户访问
        user_id = session.get('user_id', 'unknown')
        username = session.get('username', 'unknown')
        ip_address = get_client_ip(request)

        log_user_activity(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action='access_ai_assistant',
            additional_info={
                'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'unknown',
                'referrer': request.referrer if hasattr(request, 'referrer') else 'unknown'
            }
        )

        return render_template('ai_assistant.html', now=datetime.now())
    except Exception as e:
        error_msg = f"渲染AI助手页面失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()  # 打印详细错误信息

        # 记录错误
        log_system_event('ai_assistant_error', error_msg, error=e)

        return render_template('error.html', error_message="加载AI助手页面失败")

@pb.route('/verify_password', methods=['POST'])
@login_required
def verify_password():
    """验证访问密码"""
    try:
        data = request.get_json()
        password = data.get('password')

        # 获取用户信息
        user_id = session.get('user_id', 'unknown')
        username = session.get('username', 'unknown')
        ip_address = get_client_ip(request)

        if not password:
            # 记录密码为空的验证尝试
            log_user_activity(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                action='password_verification_empty',
                additional_info={
                    'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'unknown'
                }
            )

            return jsonify({
                'success': False,
                'message': '密码不能为空'
            })

        # 使用AI助手模块中的验证功能
        if verify_access_password(password):
            # 验证成功，在会话中记录验证状态
            session['ai_assistant_authenticated'] = True
            session['ai_assistant_user_id'] = str(uuid.uuid4())  # 生成唯一用户ID

            # 记录成功的验证
            log_user_activity(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                action='password_verification_success',
                additional_info={
                    'ai_assistant_user_id': session['ai_assistant_user_id'],
                    'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'unknown'
                }
            )

            return jsonify({
                'success': True,
                'message': '验证成功'
            })
        else:
            # 记录失败的验证
            log_user_activity(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                action='password_verification_failed',
                additional_info={
                    'password_length': len(password),
                    'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'unknown'
                }
            )

            return jsonify({
                'success': False,
                'message': '密码错误'
            })
    except Exception as e:
        error_msg = f"密码验证失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()

        # 记录错误
        log_system_event('password_verification_error', error_msg, error=e)

        return jsonify({
            'success': False,
            'message': f'验证请求失败: {str(e)}'
        }), 500

@pb.route('/chat', methods=['POST'])
@login_required
def chat():
    """处理聊天请求"""
    try:
        # 获取用户信息
        system_user_id = session.get('user_id', 'unknown')
        username = session.get('username', 'unknown')
        ip_address = get_client_ip(request)

        # 检查用户是否已经通过验证
        if not session.get('ai_assistant_authenticated', False):
            # 记录未验证访问尝试
            log_user_activity(
                user_id=system_user_id,
                username=username,
                ip_address=ip_address,
                action='unauthorized_chat_attempt',
                additional_info={
                    'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'unknown'
                }
            )

            return jsonify({
                'success': False,
                'message': '请先验证访问密码'
            }), 403

        data = request.get_json()
        message = data.get('message')

        if not message:
            # 记录空消息尝试
            log_user_activity(
                user_id=system_user_id,
                username=username,
                ip_address=ip_address,
                action='empty_message_attempt',
                additional_info={
                    'ai_assistant_user_id': session.get('ai_assistant_user_id', 'unknown')
                }
            )

            return jsonify({
                'success': False,
                'message': '消息不能为空'
            })

        # 获取用户ID
        ai_user_id = session.get('ai_assistant_user_id')

        # 加载聊天历史
        chat_history = load_chat_history(ai_user_id)

        # 记录用户提问
        log_user_activity(
            user_id=system_user_id,
            username=username,
            ip_address=ip_address,
            action='chat_message_sent',
            message=message,
            additional_info={
                'ai_assistant_user_id': ai_user_id,
                'message_length': len(message),
                'history_length': len(chat_history)
            }
        )

        # 调用AI助手模块获取回复
        try:
            # 获取AI回复
            response = get_chat_response(message, chat_history)

            # 更新聊天历史
            chat_history.append({
                'user': message,
                'ai': response,
                'timestamp': datetime.now().isoformat()
            })

            # 保存聊天历史
            save_chat_history(ai_user_id, chat_history)

            # 记录AI响应
            log_user_activity(
                user_id=system_user_id,
                username=username,
                ip_address=ip_address,
                action='chat_response_received',
                message=message,
                response=response,
                additional_info={
                    'ai_assistant_user_id': ai_user_id,
                    'response_length': len(response),
                    'total_messages': len(chat_history)
                }
            )

            return jsonify({
                'success': True,
                'response': response
            })

        except Exception as api_error:
            error_msg = f"API调用失败: {str(api_error)}"
            print(error_msg)
            traceback.print_exc()

            # 记录API错误
            log_system_event('api_call_error', error_msg, error=api_error)

            # 返回错误信息
            return jsonify({
                'success': False,
                'message': f'调用AI服务失败: {str(api_error)}'
            }), 500

    except Exception as e:
        error_msg = f"处理聊天请求失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()

        # 记录系统错误
        log_system_event('chat_request_error', error_msg, error=e)

        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500

@pb.route('/chat_stream', methods=['POST'])
@login_required
def chat_stream():
    """处理流式聊天请求"""
    try:
        # 获取用户信息
        system_user_id = session.get('user_id', 'unknown')
        username = session.get('username', 'unknown')
        ip_address = get_client_ip(request)

        # 检查用户是否已经通过验证
        if not session.get('ai_assistant_authenticated', False):
            # 记录未验证访问尝试
            log_user_activity(
                user_id=system_user_id,
                username=username,
                ip_address=ip_address,
                action='unauthorized_stream_attempt',
                additional_info={
                    'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'unknown'
                }
            )

            return jsonify({
                'success': False,
                'message': '请先验证访问密码'
            }), 403

        data = request.get_json()
        message = data.get('message')

        if not message:
            # 记录空消息尝试
            log_user_activity(
                user_id=system_user_id,
                username=username,
                ip_address=ip_address,
                action='empty_stream_message_attempt',
                additional_info={
                    'ai_assistant_user_id': session.get('ai_assistant_user_id', 'unknown')
                }
            )

            return jsonify({
                'success': False,
                'message': '消息不能为空'
            })

        # 获取用户ID
        ai_user_id = session.get('ai_assistant_user_id')

        # 加载聊天历史
        chat_history = load_chat_history(ai_user_id)

        # 记录用户流式提问
        log_user_activity(
            user_id=system_user_id,
            username=username,
            ip_address=ip_address,
            action='stream_message_sent',
            message=message,
            additional_info={
                'ai_assistant_user_id': ai_user_id,
                'message_length': len(message),
                'history_length': len(chat_history)
            }
        )

        def generate():
            # 初始化完整响应
            full_response = ""
            completion_sent = False
            stream_start_time = datetime.now()

            try:
                # 获取API客户端和模型ID
                from model.ai_assistant import get_api_client, get_model_id
                client = get_api_client()
                model_id = get_model_id()

                # 准备消息列表
                messages = []

                # 添加聊天历史记录（如果有）
                if chat_history:
                    for entry in chat_history:
                        if 'user' in entry and entry['user'].strip():
                            messages.append({"role": "user", "content": entry['user']})
                        if 'ai' in entry and entry['ai'].strip():
                            messages.append({"role": "assistant", "content": entry['ai']})

                # 添加当前用户消息
                messages.append({"role": "user", "content": message})

                # 调用API获取流式回复
                response = client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    stream=True,
                    max_tokens=4096,
                    temperature=0.7,
                    top_p=0.95
                )

                # 流式返回响应
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"

                # 发送完成信号
                yield f"data: {json.dumps({'content': '', 'done': True, 'full_response': full_response})}\n\n"
                completion_sent = True

                # 更新聊天历史
                chat_history.append({
                    'user': message,
                    'ai': full_response,
                    'timestamp': datetime.now().isoformat()
                })

                # 保存聊天历史
                save_chat_history(ai_user_id, chat_history)

                # 记录流式响应完成
                stream_duration = (datetime.now() - stream_start_time).total_seconds()
                log_user_activity(
                    user_id=system_user_id,
                    username=username,
                    ip_address=ip_address,
                    action='stream_response_completed',
                    message=message,
                    response=full_response,
                    additional_info={
                        'ai_assistant_user_id': ai_user_id,
                        'response_length': len(full_response),
                        'stream_duration_seconds': stream_duration,
                        'total_messages': len(chat_history)
                    }
                )

            except Exception as e:
                error_msg = f"API流式调用失败: {str(e)}"
                print(error_msg)
                traceback.print_exc()

                # 记录流式错误
                log_system_event('stream_api_error', error_msg, error=e)

                error_response = f"抱歉，在处理您的请求时遇到了问题。错误信息: {str(e)}"
                yield f"data: {json.dumps({'content': error_response, 'done': True, 'error': True})}\n\n"
                completion_sent = True

            finally:
                # 确保在所有情况下都发送完成信号
                if not completion_sent:
                    yield f"data: {json.dumps({'content': '', 'done': True, 'full_response': full_response})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        error_msg = f"处理流式聊天请求失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()

        # 记录系统错误
        log_system_event('stream_request_error', error_msg, error=e)

        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500

@pb.route('/chat_history', methods=['GET'])
@login_required
def get_chat_history():
    """获取聊天历史记录"""
    try:
        # 获取用户信息
        system_user_id = session.get('user_id', 'unknown')
        username = session.get('username', 'unknown')
        ip_address = get_client_ip(request)

        # 检查用户是否已经通过验证
        if not session.get('ai_assistant_authenticated', False):
            # 记录未验证访问尝试
            log_user_activity(
                user_id=system_user_id,
                username=username,
                ip_address=ip_address,
                action='unauthorized_history_access',
                additional_info={
                    'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'unknown'
                }
            )

            return jsonify({
                'success': False,
                'message': '请先验证访问密码'
            }), 403

        # 获取用户ID
        ai_user_id = session.get('ai_assistant_user_id')

        # 加载聊天历史
        chat_history = load_chat_history(ai_user_id)

        # 记录历史访问
        log_user_activity(
            user_id=system_user_id,
            username=username,
            ip_address=ip_address,
            action='chat_history_accessed',
            additional_info={
                'ai_assistant_user_id': ai_user_id,
                'history_count': len(chat_history)
            }
        )

        return jsonify({
            'success': True,
            'history': chat_history
        })
    except Exception as e:
        error_msg = f"获取聊天历史失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()

        # 记录错误
        log_system_event('chat_history_error', error_msg, error=e)

        return jsonify({
            'success': False,
            'message': f'获取聊天历史失败: {str(e)}'
        }), 500

@pb.route('/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    """清空聊天历史"""
    try:
        # 获取用户信息
        system_user_id = session.get('user_id', 'unknown')
        username = session.get('username', 'unknown')
        ip_address = get_client_ip(request)

        # 检查用户是否已经通过验证
        if not session.get('ai_assistant_authenticated', False):
            # 记录未验证清空尝试
            log_user_activity(
                user_id=system_user_id,
                username=username,
                ip_address=ip_address,
                action='unauthorized_clear_attempt',
                additional_info={
                    'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else 'unknown'
                }
            )

            return jsonify({
                'success': False,
                'message': '请先验证访问密码'
            }), 403

        # 获取用户ID
        ai_user_id = session.get('ai_assistant_user_id')

        # 加载当前历史记录（用于日志记录）
        current_history = load_chat_history(ai_user_id)
        history_count = len(current_history)

        # 清空聊天历史
        save_chat_history(ai_user_id, [])

        # 记录清空操作
        log_user_activity(
            user_id=system_user_id,
            username=username,
            ip_address=ip_address,
            action='chat_history_cleared',
            additional_info={
                'ai_assistant_user_id': ai_user_id,
                'cleared_history_count': history_count
            }
        )

        return jsonify({
            'success': True,
            'message': '聊天历史已清空'
        })
    except Exception as e:
        error_msg = f"清空聊天历史失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()

        # 记录错误
        log_system_event('clear_chat_error', error_msg, error=e)

        return jsonify({
            'success': False,
            'message': f'清空聊天历史失败: {str(e)}'
        }), 500
