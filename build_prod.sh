#!/bin/bash

# 数据智能分析平台 v2.0 - 生产环境构建脚本

set -e

echo "========================================="
echo "  数据智能分析平台 v2.0 生产构建"
echo "========================================="
echo ""

# 清理旧的构建
echo "🧹 清理旧构建..."
rm -rf frontend/dist

# 安装前端依赖
echo ""
echo "📦 安装前端依赖..."
cd frontend
npm install

# 构建前端
echo ""
echo "🏗️  构建前端..."
npm run build

cd ..

echo ""
echo "========================================="
echo "✅ 构建完成！"
echo "========================================="
echo ""
echo "📌 启动生产服务器："
echo ""
echo "1️⃣  直接启动："
echo "   python app.py"
echo ""
echo "2️⃣  使用 uvicorn："
echo "   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "3️⃣  使用 gunicorn (多进程)："
echo "   gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000"
echo ""
echo "4️⃣  访问应用："
echo "   http://localhost:8000"
echo ""
echo "========================================="
