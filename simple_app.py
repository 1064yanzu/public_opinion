#!/usr/bin/env python3
"""
最简单的Flask应用测试
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, Flask is working!"

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Simple Flask app is running'
    })

if __name__ == '__main__':
    print("启动简单Flask应用...")
    print("应用将在 http://localhost:5001 启动")
    try:
        app.run(debug=True, port=5001, host='0.0.0.0')
    except Exception as e:
        print(f"启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
