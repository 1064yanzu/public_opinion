#!/bin/bash

# 设置错误时退出
set -e

echo "开始部署Flask项目..."

# 更新代码
echo "正在更新代码..."
git pull

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 更新依赖
echo "更新Python依赖..."
pip install -r requirements.txt

# 重启服务
echo "重启Supervisor服务..."
sudo supervisorctl restart flask_news

# 重启Nginx
echo "重启Nginx服务..."
sudo systemctl restart nginx

# 检查服务状态
echo "检查服务状态..."
sudo supervisorctl status flask_news
sudo systemctl status nginx --no-pager

echo "部署完成！"

# 显示日志
echo "显示应用日志..."
tail -f logs/supervisor.out.log 