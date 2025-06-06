#!/bin/bash

# 设置错误时退出
set -e

echo "开始安装舆情分析系统依赖..."

# 设置环境变量
PROJECT_PATH="/www/wwwroot"
LOG_PATH="$PROJECT_PATH/logs"

# 创建日志目录
mkdir -p $LOG_PATH

# 记录安装日志
exec 1> >(tee -a "$LOG_PATH/install.log") 2>&1

echo "开始时间: $(date)"

# 确保已在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "错误：请先激活虚拟环境！"
    echo "使用命令：source py-project-env yuqing"
    exit 1
fi

echo "使用虚拟环境：$VIRTUAL_ENV"

# 配置pip源（使用阿里云镜像）
echo "配置pip源..."
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set global.trusted-host mirrors.aliyun.com

# 更新pip
echo "更新pip..."
python -m pip install --upgrade pip

# 安装基础依赖
echo "安装基础依赖..."
pip install wheel setuptools

# 安装项目依赖
echo "安装项目依赖..."
cd $PROJECT_PATH
if [ -f "requirements.txt" ]; then
    echo "从requirements.txt安装依赖..."
    # 分批安装依赖，避免单个包安装失败影响整体
    while IFS= read -r package
    do
        if [ ! -z "$package" ]; then
            echo "正在安装: $package"
            pip install "$package" || echo "警告: $package 安装失败，继续安装其他包..."
        fi
    done < requirements.txt
else
    echo "警告: requirements.txt不存在！"
    exit 1
fi

# 特别确保关键包安装
echo "确保关键包安装..."
pip install flask==2.3.3 Werkzeug==2.3.8 gunicorn==23.0.0

# 验证安装
echo "验证关键包安装..."
python -c "import flask; print('Flask版本:', flask.__version__)"
python -c "import werkzeug; print('Werkzeug版本:', werkzeug.__version__)"

# 设置项目权限
echo "设置项目权限..."
chown -R www:www $PROJECT_PATH
chmod -R 755 $PROJECT_PATH

echo "安装完成时间: $(date)"

# 显示重要信息
echo "
======================安装完成======================
1. 虚拟环境路径: $VIRTUAL_ENV
2. 项目路径: $PROJECT_PATH
3. 日志路径: $LOG_PATH

接下来的步骤：
1. 在宝塔面板的Python项目管理中：
   - 点击项目的'配置文件'
   - 确保'启动方式'选择为'gunicorn'
   - 确保'运行文件'设置为'app.py'
   - 确保'运行目录'设置为'$PROJECT_PATH'
   - 确保'虚拟环境'设置正确

2. 检查gunicorn配置：
   - 工作进程：4
   - 绑定端口：0.0.0.0:8000
   - 运行用户：www

3. 重启项目：
   - 在宝塔面板中点击'重启'按钮

4. 如果遇到问题：
   - 检查安装日志: $LOG_PATH/install.log
   - 检查项目日志: 宝塔面板Python项目管理中的'日志'
   - 检查权限问题: ls -l $PROJECT_PATH

故障排除命令：
# 手动启动服务
cd $PROJECT_PATH
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 检查进程
ps aux | grep gunicorn

# 检查端口
netstat -tlnp | grep 8000
=================================================" 