#!/bin/bash

echo "===================================="
echo "数据智能分析平台 v2.0 - 启动脚本"
echo "===================================="
echo ""

# 创建必要的目录
mkdir -p data data/users data/uploads

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python版本: $python_version"

# 检查是否已安装依赖
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "⚠️  依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

echo "✓ 依赖检查完成"

# 检查是否需要创建.env
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，从模板创建..."
    cp .env.example .env
    echo "✓ .env文件已创建，请根据需要修改配置"
fi

# 初始化管理员账户（如果不存在）
if [ ! -f data/app.db ]; then
    echo "⚠️  数据库不存在，将在首次启动时自动创建"
fi

echo ""
echo "===================================="
echo "启动FastAPI服务器..."
echo "===================================="
echo ""
echo "访问地址:"
echo "  应用主页: http://localhost:8000"
echo "  API文档:  http://localhost:8000/api/docs"
echo "  健康检查: http://localhost:8000/api/health"
echo ""
echo "首次使用请先注册账户！"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "===================================="
echo ""

# 启动服务器
python3 app.py
