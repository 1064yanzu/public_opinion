#!/bin/bash
# 后端启动脚本

# 激活虚拟环境
source .venv/bin/activate

# 切换到 backend 目录并运行
cd backend
python -m app.main
