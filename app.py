from flask import Flask,render_template,jsonify,request
from flask import send_from_directory
from werkzeug.exceptions import Forbidden, NotFound
import os
import gc
import atexit
from datetime import timedelta
# 在这里导入和注册蓝图
from views.user.user import ub
from views.page import page
from views.user import user
from model.nlp import *
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie
from spiders.articles_spider import *
from views.page.page import pb
import multiprocessing
# 性能优化相关导入
from utils.performance_monitor import performance_monitor, monitor_performance, get_performance_report
from utils.cache_manager import clear_cache, get_cache_stats, memory_cleanup
from config.settings import PERFORMANCE_CONFIG

# 尝试导入第二阶段和第三阶段模块
print("开始导入第二阶段模块...")
try:
    from utils.async_task_manager import task_manager
    print("  ✅ async_task_manager 导入成功")
    from utils.data_pipeline import crawler_pipeline
    print("  ✅ data_pipeline 导入成功")
    from utils.network_optimizer import spider_optimizer
    print("  ✅ network_optimizer 导入成功")
    print("第二阶段模块导入成功")
except ImportError as e:
    print(f"第二阶段模块导入失败: {str(e)}")
    task_manager = None
    crawler_pipeline = None
    spider_optimizer = None

print("开始导入第三阶段模块...")
try:
    from utils.advanced_cache import advanced_cache
    print("  ✅ advanced_cache 导入成功")
    from utils.frontend_optimizer import init_frontend_optimization, static_optimizer, page_optimizer, cdn_optimizer
    print("  ✅ frontend_optimizer 导入成功")
    from utils.monitoring_alerts import alert_manager
    print("  ✅ monitoring_alerts 导入成功")
    from utils.smart_preprocessor import smart_preprocessor
    print("  ✅ smart_preprocessor 导入成功")
    print("第三阶段模块导入成功")
except ImportError as e:
    print(f"第三阶段模块导入失败: {str(e)}")
    advanced_cache = None
    init_frontend_optimization = None
    static_optimizer = None
    page_optimizer = None
    cdn_optimizer = None
    alert_manager = None
    smart_preprocessor = None

print("创建Flask应用实例...")
app = Flask(__name__)
print("Flask应用实例创建成功")

# Session配置 - 从环境变量获取密钥
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # session有效期7天
app.config['SESSION_COOKIE_NAME'] = 'session'  # session cookie名称
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止XSS攻击
app.config['SESSION_COOKIE_SECURE'] = False  # 如果使用HTTPS，设置为True
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # 每次请求都刷新session
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统存储session

# 性能优化配置
app.config['JSON_SORT_KEYS'] = False  # 不排序JSON键，提升性能
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # 不美化JSON输出
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 启用压缩（如果有Flask-Compress）
try:
    from flask_compress import Compress
    Compress(app)
    print("已启用响应压缩")
except ImportError:
    print("Flask-Compress未安装，跳过压缩配置")

# 初始化第三阶段优化功能
print("初始化第三阶段性能优化功能...")

# 初始化前端优化（简化版本）
if init_frontend_optimization:
    init_frontend_optimization(app)
    print("前端优化已初始化")

# 启动系统监控
if alert_manager and PERFORMANCE_CONFIG.get('enable_monitoring', True):
    alert_manager.start_monitoring()
    print("系统监控告警已启动")

print("第三阶段优化功能初始化完成")

print("注册蓝图...")
app.register_blueprint(page.pb)
print("  ✅ page蓝图注册成功")
app.register_blueprint(user.ub)
print("  ✅ user蓝图注册成功")
print("蓝图注册完成")

@app.route('/')
def hello_world():  # put application's code here
    return render_template('welcome.html')

@app.route('/test')
def test():
    """测试页面，检查静态文件"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>静态文件测试</title>
        <link rel="stylesheet" href="/static/assets/css/modern.css">
    </head>
    <body>
        <h1>静态文件测试页面</h1>
        <p>如果这个页面有样式，说明CSS文件加载成功。</p>
        <script src="/static/assets/js/cropper.min.js"></script>
        <script>
            console.log("JS文件加载成功");
            document.body.style.backgroundColor = "#f0f0f0";
        </script>
    </body>
    </html>
    '''


@app.errorhandler(Exception)
def handle_exception(e):
    # 获取错误信息
    error_message = str(e)

    # 可以根据不同的异常类型返回不同的状态码
    if isinstance(e, NotFound):
        status_code = 404
    elif isinstance(e, Forbidden):
        status_code = 403
    else:
        status_code = 500

    # 渲染错误页面
    return render_template('error.html', error_message=error_message), status_code


@app.route('/get_chart_data')
@monitor_performance('chart_data_generation')
def get_chart_data():
    try:
        infos2, share_num, comment_num, like_num = get_info2(ready_path)
        pie = (
            Pie()
            .add("", [("转发数", share_num), ("点赞数", like_num), ("评论数", comment_num)])
            .set_global_opts(title_opts=opts.TitleOpts(title="ECharts 饼图示例"))
        )
        # 将图表转换为 JSON 字符串发送给前端
        return jsonify(pie.dump_options_with_quotes())
    except Exception as e:
        print(f"图表数据生成失败: {str(e)}")
        return jsonify({'error': '图表数据生成失败'}), 500


@app.route('/search', methods=['POST'])
@monitor_performance('weibo_search')
def search():
    try:
        keyword = request.form.get('keyword')
        max_page = int(request.form.get('max_page', 10))  # 默认为10页
        async_mode = request.form.get('async', 'false').lower() == 'true'

        # 参数验证
        if not keyword or not keyword.strip():
            return jsonify({'error': '关键词不能为空'}), 400

        if max_page < 1 or max_page > 50:  # 限制最大页数
            max_page = min(max(max_page, 1), 50)

        keyword = keyword.strip()

        if async_mode and task_manager:
            # 异步处理
            task_id = task_manager.submit_task(
                get_weibo_list,
                keyword,
                max_page,
                task_id=f"weibo_search_{keyword}_{int(time.time())}"
            )
            return jsonify({
                'task_id': task_id,
                'message': '搜索任务已提交，请使用task_id查询结果',
                'status_url': f'/api/tasks/{task_id}'
            })
        elif async_mode and not task_manager:
            return jsonify({'error': '异步任务管理器未启用，请使用同步模式'}), 503
        else:
            # 同步处理
            results = get_weibo_list(keyword, max_page)
            return jsonify(results)

    except Exception as e:
        print(f"搜索失败: {str(e)}")
        return jsonify({'error': '搜索失败'}), 500


@app.route('/search/douyin', methods=['POST'])
@monitor_performance('douyin_search')
def search_douyin():
    """抖音搜索接口"""
    try:
        keyword = request.form.get('keyword')
        max_page = int(request.form.get('max_page', 5))  # 默认为5页
        async_mode = request.form.get('async', 'false').lower() == 'true'

        # 参数验证
        if not keyword or not keyword.strip():
            return jsonify({'error': '关键词不能为空'}), 400

        if max_page < 1 or max_page > 20:  # 限制最大页数
            max_page = min(max(max_page, 1), 20)

        keyword = keyword.strip()

        if async_mode and task_manager:
            # 异步处理
            from spiders.douyin import get_douyin_list
            task_id = task_manager.submit_task(
                get_douyin_list,
                keyword,
                max_page,
                task_id=f"douyin_search_{keyword}_{int(time.time())}"
            )
            return jsonify({
                'task_id': task_id,
                'message': '抖音搜索任务已提交，请使用task_id查询结果',
                'status_url': f'/api/tasks/{task_id}'
            })
        elif async_mode and not task_manager:
            return jsonify({'error': '异步任务管理器未启用，请使用同步模式'}), 503
        else:
            # 同步处理
            from spiders.douyin import get_douyin_list
            results = get_douyin_list(keyword, max_page)
            return jsonify(results)

    except Exception as e:
        print(f"抖音搜索失败: {str(e)}")
        return jsonify({'error': '抖音搜索失败'}), 500


# 性能监控相关路由
@app.route('/api/performance/stats')
def performance_stats():
    """获取性能统计信息"""
    try:
        stats = get_performance_report()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/stats')
def cache_stats():
    """获取缓存统计信息"""
    try:
        stats = get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache_api():
    """清空缓存"""
    try:
        clear_cache()
        return jsonify({'message': '缓存已清空'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 异步任务管理相关路由
@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务状态"""
    try:
        if task_manager:
            tasks = task_manager.get_all_tasks()
            return jsonify(tasks)
        else:
            return jsonify({'error': '任务管理器未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取特定任务状态"""
    try:
        if task_manager:
            status = task_manager.get_task_status(task_id)
            return jsonify(status)
        else:
            return jsonify({'error': '任务管理器未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    try:
        if task_manager:
            success = task_manager.cancel_task(task_id)
            if success:
                return jsonify({'message': f'任务 {task_id} 已取消'})
            else:
                return jsonify({'message': f'任务 {task_id} 无法取消'}), 400
        else:
            return jsonify({'error': '任务管理器未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crawler/stats', methods=['GET'])
def get_crawler_stats():
    """获取爬虫统计信息"""
    try:
        if spider_optimizer:
            stats = spider_optimizer.get_stats()
            return jsonify(stats)
        else:
            return jsonify({'error': '爬虫优化器未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 第三阶段新增API端点

@app.route('/api/cache/advanced/stats', methods=['GET'])
def get_advanced_cache_stats():
    """获取高级缓存统计信息"""
    try:
        if advanced_cache:
            stats = advanced_cache.get_stats()
            return jsonify(stats)
        else:
            return jsonify({'error': '高级缓存未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/advanced/clear', methods=['POST'])
def clear_advanced_cache():
    """清空高级缓存"""
    try:
        if advanced_cache:
            advanced_cache.clear()
            return jsonify({'message': '高级缓存已清空'})
        else:
            return jsonify({'error': '高级缓存未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitoring/alerts', methods=['GET'])
def get_alerts():
    """获取告警信息"""
    try:
        if alert_manager:
            limit = request.args.get('limit', 50, type=int)
            alerts = alert_manager.get_alert_history(limit)
            return jsonify(alerts)
        else:
            return jsonify({'error': '监控告警未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitoring/alerts/stats', methods=['GET'])
def get_alert_stats():
    """获取告警统计信息"""
    try:
        if alert_manager:
            stats = alert_manager.get_alert_stats()
            return jsonify(stats)
        else:
            return jsonify({'error': '监控告警未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitoring/check', methods=['POST'])
def manual_alert_check():
    """手动触发告警检查"""
    try:
        if alert_manager:
            alerts = alert_manager.check_alerts()
            return jsonify({
                'message': '告警检查完成',
                'triggered_alerts': len(alerts),
                'alerts': alerts
            })
        else:
            return jsonify({'error': '监控告警未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preprocessing/stats', methods=['GET'])
def get_preprocessing_stats():
    """获取数据预处理统计信息"""
    try:
        if smart_preprocessor:
            stats = smart_preprocessor.get_stats()
            return jsonify(stats)
        else:
            return jsonify({'error': '智能预处理器未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/frontend/stats', methods=['GET'])
def get_frontend_stats():
    """获取前端优化统计信息"""
    try:
        if static_optimizer and cdn_optimizer:
            stats = {
                'static_optimizer': static_optimizer.get_stats(),
                'cdn_optimizer': {
                    'available_libraries': list(cdn_optimizer.cdn_configs.keys())
                }
            }
            return jsonify(stats)
        else:
            return jsonify({'error': '前端优化器未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500





@app.teardown_appcontext
def shutdown_session(exception=None):
    """应用上下文清理"""
    # exception参数由Flask框架传入，即使不使用也需要保留
    try:
        # 清理多进程
        for child in multiprocessing.active_children():
            child.terminate()
            child.join()

        # 定期内存清理
        if hasattr(shutdown_session, 'call_count'):
            shutdown_session.call_count += 1
        else:
            shutdown_session.call_count = 1

        # 每100次请求清理一次内存
        if shutdown_session.call_count % 100 == 0:
            gc.collect()
            print(f"执行内存清理，请求计数: {shutdown_session.call_count}")

    except Exception as e:
        print(f"清理过程出错: {str(e)}")


def cleanup_on_exit():
    """应用退出时的清理函数"""
    print("应用正在退出，执行清理...")
    try:
        # 停止系统监控
        if alert_manager:
            alert_manager.stop_monitoring()

        # 关闭异步任务管理器
        if task_manager:
            task_manager.shutdown()

        # 关闭网络优化器
        if spider_optimizer:
            spider_optimizer.close()

        # 清理所有缓存
        memory_cleanup()
        if advanced_cache:
            advanced_cache.clear()

        # 重置预处理器统计
        if smart_preprocessor:
            smart_preprocessor.reset_stats()

        # 清理多进程
        for child in multiprocessing.active_children():
            child.terminate()
            child.join()

        # 强制垃圾回收
        gc.collect()
        print("清理完成")
    except Exception as e:
        print(f"退出清理失败: {str(e)}")


# 注册退出清理函数
atexit.register(cleanup_on_exit)

if __name__ == '__main__':
    print("启动Flask应用...")
    print(f"性能配置: {PERFORMANCE_CONFIG}")

    # 显示应用信息
    print(f"应用名称: {app.name}")
    print(f"注册的蓝图: {list(app.blueprints.keys())}")
    print(f"路由数量: {len(app.url_map._rules)}")

    # 显示主要路由
    print("主要路由:")
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/static'):
            print(f"  {rule.rule} -> {rule.endpoint}")

    print("应用即将启动在 http://0.0.0.0:5000")

    try:
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=5000,
            threaded=True,
            debug=False,  # 生产环境关闭调试模式
            use_reloader=False  # 避免重复加载
        )
    except Exception as e:
        print(f"应用启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
