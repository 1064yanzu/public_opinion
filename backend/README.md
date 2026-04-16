# FastAPI 舆情分析系统 - 后端

基于 FastAPI + SQLite 的现代化舆情分析系统后端。

## 技术栈

- **框架**: FastAPI 0.115+
- **数据库**: SQLite 3 + SQLAlchemy 2.0
- **异步支持**: aiosqlite
- **数据迁移**: Alembic
- **认证**: JWT (python-jose + passlib)

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，修改必要的配置
```

### 3. 初始化数据库

```bash
# 数据库会在首次启动时自动创建
# 或手动运行初始化脚本
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 4. 启动开发服务器

```bash
# 方式1：使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式2：直接运行
python -m app.main
```

访问 API 文档：http://localhost:8000/docs

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy 数据模型
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── weibo.py
│   │   ├── douyin.py
│   │   └── hotspot.py
│   ├── schemas/             # Pydantic 模式（TODO）
│   └── routers/             # API 路由（TODO）
├── alembic/                 # 数据库迁移
├── scripts/                 # 工具脚本
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量示例
└── README.md
```

## 数据库模型

- **users**: 用户表
- **tasks**: 任务表
- **weibo_data**: 微博数据表
- **douyin_data**: 抖音数据表
- **hotspots**: 热点数据表

详细设计参考：[docs/database_design.md](../docs/database_design.md)

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

参考：[docs/development.md](../docs/development.md)

## 部署

参考：[docs/deployment.md](../docs/deployment.md)
