#!/bin/bash

# 设置环境变量
export PYTHONPATH=/www/wwwroot/flask
export FLASK_APP=app.py
export FLASK_ENV=production
export PYTHONUNBUFFERED=1  # 禁用Python输出缓冲
export PYTHONDONTWRITEBYTECODE=1  # 不生成pyc文件

# 激活虚拟环境
source /www/server/pyporject_evn/flask_venv/bin/activate

# 确保目录存在
mkdir -p /www/wwwroot/flask/logs

# 清理旧的日志文件
echo "" > /www/wwwroot/flask/logs/error.log
echo "" > /www/wwwroot/flask/logs/access.log

# 启动应用
cd /www/wwwroot/flask
gunicorn app:app \
    --workers 2 \
    --threads 2 \
    --bind 0.0.0.0:8000 \
    --access-logfile /www/wwwroot/flask/logs/access.log \
    --error-logfile /www/wwwroot/flask/logs/error.log \
    --capture-output \
    --log-level debug \
    --timeout 120 \
    --reload \
    2>&1 | tee -a /www/wwwroot/flask/logs/startup.log 