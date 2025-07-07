#!/usr/bin/env python3
"""
调试版Flask应用 - 逐步添加功能来找出问题
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始导入基础模块...")

from flask import Flask, jsonify, render_template, request
print("✅ Flask导入成功")

from werkzeug.exceptions import Forbidden, NotFound
print("✅ Werkzeug导入成功")

import gc
import atexit
from datetime import timedelta
print("✅ 标准库导入成功")

print("开始导入项目模块...")

try:
    from views.user.user import ub
    print("✅ views.user.user导入成功")
except Exception as e:
    print(f"❌ views.user.user导入失败: {str(e)}")
    ub = None

try:
    from views.page import page
    print("✅ views.page导入成功")
except Exception as e:
    print(f"❌ views.page导入失败: {str(e)}")
    page = None

try:
    from views.user import user
    print("✅ views.user导入成功")
except Exception as e:
    print(f"❌ views.user导入失败: {str(e)}")
    user = None

print("开始导入性能监控模块...")

try:
    from utils.performance_monitor import performance_monitor, monitor_performance, get_performance_report
    print("✅ performance_monitor导入成功")
except Exception as e:
    print(f"❌ performance_monitor导入失败: {str(e)}")
    performance_monitor = None
    monitor_performance = lambda x: lambda f: f
    get_performance_report = lambda: {}

try:
    from utils.cache_manager import clear_cache, get_cache_stats, memory_cleanup
    print("✅ cache_manager导入成功")
except Exception as e:
    print(f"❌ cache_manager导入失败: {str(e)}")
    clear_cache = lambda: None
    get_cache_stats = lambda: {}
    memory_cleanup = lambda: None

try:
    from config.settings import PERFORMANCE_CONFIG
    print("✅ config.settings导入成功")
except Exception as e:
    print(f"❌ config.settings导入失败: {str(e)}")
    PERFORMANCE_CONFIG = {}

print("创建Flask应用...")
app = Flask(__name__)
print("✅ Flask应用创建成功")

print("配置Flask应用...")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'debug-secret-key-123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
print("✅ Flask应用配置完成")

print("注册蓝图...")
if page and hasattr(page, 'pb'):
    app.register_blueprint(page.pb)
    print("✅ page蓝图注册成功")

if user and hasattr(user, 'ub'):
    app.register_blueprint(user.ub)
    print("✅ user蓝图注册成功")

print("定义路由...")

@app.route('/')
def index():
    return "<h1>调试Flask应用正常运行!</h1><p><a href='/api/health'>健康检查</a></p>"

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Debug Flask app is working',
        'modules': {
            'views_user': ub is not None,
            'views_page': page is not None,
            'performance_monitor': performance_monitor is not None,
            'cache_manager': clear_cache is not None,
            'config_settings': bool(PERFORMANCE_CONFIG)
        }
    })

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

print("路由定义完成")

def cleanup_on_exit():
    """应用退出时的清理函数"""
    print("应用正在退出，执行清理...")
    try:
        memory_cleanup()
        gc.collect()
        print("清理完成")
    except Exception as e:
        print(f"退出清理失败: {str(e)}")

# 注册退出清理函数
atexit.register(cleanup_on_exit)

if __name__ == '__main__':
    print("=" * 60)
    print("启动调试Flask应用")
    print("URL: http://localhost:5000")
    print("健康检查: http://localhost:5000/api/health")
    print("=" * 60)
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"应用启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
