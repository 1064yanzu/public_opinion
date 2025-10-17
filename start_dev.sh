#!/bin/bash

# 数据智能分析平台 v2.0 - 开发环境启动脚本

set -e

echo "========================================="
echo "  数据智能分析平台 v2.0 开发环境启动"
echo "========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data data/users data/uploads

# 安装 Python 依赖
echo ""
echo "📦 安装 Python 依赖..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r backend/requirements.txt

# 初始化数据库
echo ""
echo "🗄️  初始化数据库..."
python init_admin.py

# 安装前端依赖
echo ""
echo "📦 安装前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

echo ""
echo "========================================="
echo "✅ 环境准备完成！"
echo "========================================="
echo ""
echo "📌 启动方式："
echo ""
echo "1️⃣  启动后端（终端1）："
echo "   python app.py"
echo "   或"
echo "   uvicorn backend.app.main:app --reload"
echo ""
echo "2️⃣  启动前端开发服务器（终端2）："
echo "   cd frontend && npm run dev"
echo ""
echo "3️⃣  访问应用："
echo "   前端开发: http://localhost:5173"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/api/docs"
echo ""
echo "🔑 默认管理员账号："
echo "   用户名: admin"
echo "   密码:   admin123"
echo ""
echo "========================================="
