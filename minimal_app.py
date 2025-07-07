#!/usr/bin/env python3
"""
最小化Flask应用 - 用于测试基础功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Flask应用正常运行!</h1><p><a href='/api/health'>健康检查</a></p>"

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Minimal Flask app is working',
        'routes': [
            '/',
            '/api/health'
        ]
    })

if __name__ == '__main__':
    print("=" * 50)
    print("启动最小化Flask应用")
    print("URL: http://localhost:5000")
    print("健康检查: http://localhost:5000/api/health")
    print("=" * 50)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=False
    )
