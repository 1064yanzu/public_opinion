#!/usr/bin/env python3
"""
简化的页面服务器 - 用于预览模板更改
仅提供静态模板渲染和API模拟
"""
from flask import Flask, render_template, jsonify, request
import os
import time

# 创建Flask应用
app = Flask(__name__, 
           template_folder='views/page/templates',
           static_folder='views/page/static')

# 模拟数据
def get_mock_home_data():
    """返回模拟的首页数据用于测试"""
    return {
        'success': True,
        'data': {
            'row_count': 1234,
            'unique_user_count': 567,
            'unique_ip_count': 89,
            'total_heat_value': 9876,
            'infos2_data': [
                {
                    'author': '用户A',
                    'content': '这是一条模拟微博内容，用于测试异步加载效果',
                    'time': '2025-01-07 15:30:00',
                    'shares': 10,
                    'comments': 25, 
                    'likes': 88,
                    'url': 'https://example.com/post1',
                    'profile_url': 'https://example.com/user1'
                },
                {
                    'author': '用户B',
                    'content': '第二条测试数据，验证表格渲染功能',
                    'time': '2025-01-07 14:20:00',
                    'shares': 5,
                    'comments': 12,
                    'likes': 45,
                    'url': 'https://example.com/post2'
                },
                {
                    'author': '用户C',
                    'content': '第三条测试内容，用于检验分页显示',
                    'time': '2025-01-07 13:15:00',
                    'shares': 8,
                    'comments': 18,
                    'likes': 67
                }
            ],
            'daily_hotspots': [
                {
                    'title': '测试热点新闻标题A',
                    'link': 'https://example.com/news1',
                    'source': '测试来源A'
                },
                {
                    'title': '测试热点新闻标题B',
                    'link': 'https://example.com/news2', 
                    'source': '测试来源B'
                },
                {
                    'title': '测试热点新闻标题C',
                    'link': 'https://example.com/news3',
                    'source': '测试来源C'
                }
            ]
        }
    }

@app.route('/')
def index():
    """首页路由 - 返回骨架屏模板"""
    return render_template('index.html', skeleton_mode=True)

@app.route('/page/api/home-data', endpoint='page.get_home_data')
def page_get_home_data():
    return jsonify(get_mock_home_data())

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'server': 'Simple Page Server',
        'purpose': 'Template Preview Only'
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("简化页面服务器启动")
    print("用途: 预览模板更改")
    print("URL: http://127.0.0.1:8080")
    print("API测试: http://127.0.0.1:8080/api/home-data")
    print("=" * 60)
    
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True,
        use_reloader=False
    )