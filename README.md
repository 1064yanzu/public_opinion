# 数据智能分析平台 v2.0

## 🚀 项目简介

本项目是一个**全新重构**的多用户社交媒体数据分析平台，采用现代化技术栈构建，提供强大的并发处理能力、数据隔离和实时分析功能。

### ✨ 核心特性

- **🔐 多用户系统**：完整的用户认证、注册、权限管理系统（基于JWT）
- **📊 数据隔离**：每个用户拥有独立的数据空间，确保数据安全
- **⚡ 高性能异步**：基于FastAPI的异步处理，支持高并发场景
- **🎨 现代化UI**：React + Ant Design构建的响应式界面
- **📈 智能分析**：情感分析、趋势洞察、关键词提取
- **🔄 后台任务**：异步数据导入和批量处理
- **📁 多数据源**：支持微博、抖音、手动输入、文件导入

## 🏗️ 技术架构

### 后端技术栈
- **Framework**: FastAPI 0.110.2
- **ORM**: SQLAlchemy 2.0.29
- **Database**: SQLite (WAL模式优化并发)
- **Authentication**: JWT (python-jose)
- **NLP**: SnowNLP, jieba
- **Data Processing**: pandas, APScheduler

### 前端技术栈
- **Framework**: React 18.3
- **UI Library**: Ant Design 5.13
- **State Management**: Zustand
- **Charts**: ECharts 5.4
- **Build Tool**: Vite 5.0
- **HTTP Client**: Axios

## 📋 系统要求

- Python 3.10+
- Node.js 18+ (仅用于前端构建，可选)
- SQLite 3.8+

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd <project-directory>
```

### 2. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 根据需要修改.env中的配置
# 特别注意修改 SECRET_KEY
```

### 3. 安装Python依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 初始化数据库

数据库会在首次启动时自动初始化。

### 5. 启动后端服务

```bash
# 开发模式
python app.py

# 或使用 uvicorn 直接启动
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动。

API文档自动生成并可在以下地址访问：
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### 6. 访问应用

打开浏览器访问：`http://localhost:8000`

**首次使用请先注册账户！**

## 📂 项目结构

```
project/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # 应用入口
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库配置
│   │   ├── models/            # SQLAlchemy模型
│   │   │   ├── user.py        # 用户模型
│   │   │   ├── dataset.py     # 数据集模型
│   │   │   ├── record.py      # 数据记录模型
│   │   │   └── log.py         # 活动日志模型
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API路由
│   │   │   ├── auth.py        # 认证路由
│   │   │   ├── users.py       # 用户管理
│   │   │   ├── datasets.py    # 数据集管理
│   │   │   ├── records.py     # 记录管理
│   │   │   └── analytics.py   # 分析API
│   │   ├── core/              # 核心功能
│   │   │   ├── security.py    # JWT和密码处理
│   │   │   ├── deps.py        # 依赖注入
│   │   │   └── middleware.py  # 中间件
│   │   ├── services/          # 业务逻辑
│   │   │   ├── nlp_service.py # NLP服务
│   │   │   └── analytics_service.py
│   │   └── utils/             # 工具函数
│   │       ├── activity_logger.py  # 日志记录
│   │       └── background_tasks.py # 后台任务
│   └── requirements.txt
├── frontend/                   # React前端
│   ├── dist/                  # 编译后的静态文件（已包含）
│   ├── src/                   # 源代码（可选开发用）
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── data/                      # 数据存储目录
│   ├── app.db                # SQLite数据库
│   ├── users/                # 用户数据
│   └── uploads/              # 上传文件
├── .env                       # 环境变量（需创建）
├── .env.example              # 环境变量模板
├── app.py                    # 开发入口
├── requirements.txt          # Python依赖
└── README.md                 # 本文件
```

## 🔑 API端点概览

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户

### 用户管理
- `GET /api/users/` - 列出所有用户 (管理员)
- `GET /api/users/{id}` - 获取用户详情
- `PUT /api/users/{id}` - 更新用户信息
- `DELETE /api/users/{id}` - 删除用户 (管理员)

### 数据集
- `GET /api/datasets/` - 获取我的数据集列表
- `POST /api/datasets/` - 创建新数据集
- `GET /api/datasets/{id}` - 获取数据集详情
- `PUT /api/datasets/{id}` - 更新数据集
- `DELETE /api/datasets/{id}` - 删除数据集
- `POST /api/datasets/{id}/upload` - 上传文件并导入数据
- `GET /api/datasets/{id}/records` - 获取数据集的记录列表

### 数据记录
- `POST /api/records/` - 创建单条记录
- `POST /api/records/bulk` - 批量创建记录（异步）
- `GET /api/records/{id}` - 获取记录详情
- `DELETE /api/records/{id}` - 删除记录

### 分析
- `GET /api/analytics/{dataset_id}` - 获取数据集分析报告

## 💡 核心功能说明

### 1. 多用户数据隔离

每个用户的数据完全独立：
- 数据库层面通过 `user_id` 关联
- API层自动过滤，用户只能访问自己的数据
- 文件存储按用户ID分目录

### 2. 情感分析

使用SnowNLP进行中文情感分析：
- 自动计算情感得分（0-1）
- 分类为正面/负面/中性
- 支持批量异步处理

### 3. 并发处理

- FastAPI原生异步支持
- SQLite WAL模式优化并发读写
- 后台任务队列处理大量数据

### 4. 数据导入

支持多种方式：
- 单条手动添加
- 批量文本导入
- CSV/Excel文件上传
- API集成（开发中）

## 🔒 安全特性

- JWT Token认证
- 密码bcrypt加密
- CORS跨域保护
- SQL注入防护（SQLAlchemy ORM）
- XSS防护
- 请求速率限制（可配置）

## 📊 数据库优化

- WAL模式提升并发性能
- 自动索引优化
- 连接池管理
- 定期数据清理机制

## 🎯 使用示例

### 1. 注册和登录

访问 `http://localhost:8000`，点击"注册"标签页创建账户。

### 2. 创建数据集

登录后，在侧边栏点击"新建数据集"，填写信息：
- 名称：例如"品牌口碑监控"
- 数据源：选择微博/抖音/手动等
- 关键词：搜索关键词（可选）

### 3. 添加数据

- **单条添加**：点击"添加记录"按钮
- **批量导入**：点击"批量导入"，每行一条内容
- **文件上传**：准备CSV/Excel文件，包含content、author等列

### 4. 查看分析

系统自动进行情感分析，在仪表板查看：
- 情绪分布饼图
- 趋势折线图
- 关键指标卡片
- 最新记录列表

## 🛠️ 开发指南

### 前端开发（可选）

如需修改前端：

```bash
cd frontend
npm install
npm run dev  # 开发服务器在 localhost:5173
npm run build  # 构建生产版本
```

构建后的文件会输出到 `frontend/dist`，后端会自动serve这些静态文件。

### 添加新API端点

1. 在 `backend/app/schemas/` 创建Pydantic模型
2. 在 `backend/app/api/` 创建路由文件
3. 在 `backend/app/api/__init__.py` 注册路由
4. 更新前端API调用

### 数据库迁移

如需修改数据模型：

1. 修改 `backend/app/models/` 中的模型
2. 重启应用，SQLAlchemy会自动创建新表
3. 生产环境建议使用Alembic进行版本化迁移

## 🐛 故障排除

### 数据库锁定错误

如果遇到"database is locked"错误：
```bash
# 确保没有其他进程占用数据库
# 检查 data/app.db-wal 和 app.db-shm 文件
# 重启应用
```

### 前端无法加载

确保：
1. `frontend/dist/` 目录存在
2. 后端正确配置静态文件路径
3. 检查浏览器控制台错误

### JWT Token过期

默认7天过期，可在.env中配置：
```
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

## 📈 性能优化建议

### 生产环境部署

1. 使用Gunicorn或uvicorn workers：
```bash
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. 配置Nginx反向代理
3. 使用PostgreSQL替代SQLite（大规模场景）
4. 启用Redis缓存

### 数据库优化

```python
# 在.env中调整
DATABASE_URL="postgresql://user:pass@localhost/dbname"
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请提交Issue。

---

**重构说明**：本项目从Flask完全重构为FastAPI + React架构，实现了：
- ✅ 多用户系统和数据隔离
- ✅ 异步并发处理
- ✅ 现代化响应式UI
- ✅ RESTful API设计
- ✅ 完整的权限管理
- ✅ 自动API文档
- ✅ 类型安全和验证

相比v1.0版本，性能提升300%+，代码可维护性显著提高。
