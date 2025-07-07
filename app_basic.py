"""
Flask应用基础版本 - 仅包含核心功能，用于测试和调试
"""
import os
import gc
import atexit
import multiprocessing
from datetime import timedelta
from flask import Flask, render_template, jsonify, request, send_from_directory
from werkzeug.exceptions import Forbidden

# 基础导入
from views.user.user import ub
from views.page import page
from views.user import user
from model.nlp import *
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie
from spiders.articles_spider import *
from views.page.page import pb

# 第一阶段优化导入
try:
    from utils.performance_monitor import get_performance_report
    from utils.cache_manager import clear_cache, get_cache_stats, memory_cleanup
    from config.settings import PERFORMANCE_CONFIG
    print("第一阶段优化模块导入成功")
except ImportError as e:
    print(f"第一阶段优化模块导入失败: {str(e)}")
    PERFORMANCE_CONFIG = {}

app = Flask(__name__)

# Session配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_TYPE'] = 'filesystem'

# 性能优化配置
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

print("Flask应用基础配置完成")

# 注册蓝图
app.register_blueprint(ub, url_prefix='/user')
app.register_blueprint(pb, url_prefix='/page')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_chart_data')
def get_chart_data():
    try:
        infos2, share_num, comment_num, like_num = get_info2(ready_path)
        pie = (
            Pie()
            .add("", [("转发数", share_num), ("点赞数", like_num), ("评论数", comment_num)])
            .set_global_opts(title_opts=opts.TitleOpts(title="ECharts 饼图示例"))
        )
        return jsonify(pie.dump_options_with_quotes())
    except Exception as e:
        print(f"图表数据生成失败: {str(e)}")
        return jsonify({'error': '图表数据生成失败'}), 500

@app.route('/search', methods=['POST'])
def search():
    try:
        keyword = request.form.get('keyword')
        max_page = int(request.form.get('max_page', 10))
        
        if not keyword or not keyword.strip():
            return jsonify({'error': '关键词不能为空'}), 400
        
        if max_page < 1 or max_page > 50:
            max_page = min(max(max_page, 1), 50)
        
        # 同步处理
        results = get_weibo_list(keyword.strip(), max_page)
        return jsonify(results)
        
    except Exception as e:
        print(f"搜索失败: {str(e)}")
        return jsonify({'error': '搜索失败'}), 500

@app.route('/search/douyin', methods=['POST'])
def search_douyin():
    """抖音搜索接口"""
    try:
        keyword = request.form.get('keyword')
        max_page = int(request.form.get('max_page', 5))
        
        if not keyword or not keyword.strip():
            return jsonify({'error': '关键词不能为空'}), 400
        
        if max_page < 1 or max_page > 20:
            max_page = min(max(max_page, 1), 20)
        
        # 同步处理
        from spiders.douyin import get_douyin_list
        results = get_douyin_list(keyword.strip(), max_page)
        return jsonify(results)
        
    except Exception as e:
        print(f"抖音搜索失败: {str(e)}")
        return jsonify({'error': '抖音搜索失败'}), 500

# 基础性能监控API
@app.route('/api/performance/stats')
def performance_stats():
    """获取性能统计信息"""
    try:
        if 'get_performance_report' in globals():
            stats = get_performance_report()
            return jsonify(stats)
        else:
            return jsonify({'error': '性能监控未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/stats')
def cache_stats():
    """获取缓存统计信息"""
    try:
        if 'get_cache_stats' in globals():
            stats = get_cache_stats()
            return jsonify(stats)
        else:
            return jsonify({'error': '缓存未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache_api():
    """清空缓存"""
    try:
        if 'clear_cache' in globals():
            clear_cache()
            return jsonify({'message': '缓存已清空'})
        else:
            return jsonify({'error': '缓存未启用'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'version': 'basic',
        'features': {
            'performance_monitor': 'get_performance_report' in globals(),
            'cache_manager': 'get_cache_stats' in globals(),
            'async_tasks': False,
            'advanced_cache': False,
            'monitoring_alerts': False
        }
    })

@app.teardown_appcontext
def shutdown_session(exception=None):
    """应用上下文清理"""
    try:
        for child in multiprocessing.active_children():
            child.terminate()
            child.join()
        
        # 定期内存清理
        if hasattr(shutdown_session, 'call_count'):
            shutdown_session.call_count += 1
        else:
            shutdown_session.call_count = 1
        
        if shutdown_session.call_count % 100 == 0:
            gc.collect()
            print(f"执行内存清理，请求计数: {shutdown_session.call_count}")
            
    except Exception as e:
        print(f"清理过程出错: {str(e)}")

def cleanup_on_exit():
    """应用退出时的清理函数"""
    print("应用正在退出，执行清理...")
    try:
        # 清理缓存
        if 'memory_cleanup' in globals():
            memory_cleanup()
        
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
    print("启动Flask应用（基础版本）...")
    print(f"性能配置: {PERFORMANCE_CONFIG}")
    
    app.run(
        threaded=True,
        debug=False,
        use_reloader=False,
        port=5000
    )
