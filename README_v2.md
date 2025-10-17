# 数据智能分析平台 v2.0

> 基于 FastAPI + React + SQLite 的现代化多用户数据分析平台

## ✨ 特性

- 🔐 **JWT 认证系统** - 安全的用户认证与授权
- 👥 **多用户支持** - 完整的数据隔离机制
- 📊 **情感分析** - 基于 SnowNLP 的中文情感分析
- 📈 **数据可视化** - ECharts 交互式图表
- 🎨 **现代化 UI** - Ant Design + 渐变色设计
- 🚀 **高性能** - FastAPI 异步处理 + SQLite WAL 模式
- 📦 **解耦架构** - 前后端分离，API 优先设计

## 🛠️ 技术栈

### 后端
- **FastAPI 0.110.2** - 现代化 Python Web 框架
- **SQLAlchemy 2.0.29** - ORM 数据库操作
- **Pydantic 2.10+** - 数据验证
- **JWT** - Token 认证
- **SnowNLP + Jieba** - 中文 NLP 处理
- **pandas** - 数据处理
- **APScheduler** - 定时任务

### 前端
- **React 18.3** - UI 框架
- **TypeScript** - 类型安全
- **Ant Design 5** - UI 组件库
- **ECharts 5** - 数据可视化
- **Zustand** - 状态管理
- **Vite 5** - 构建工具
- **Axios** - HTTP 客户端

### 数据库
- **SQLite** - 轻量级数据库，WAL 模式支持并发

## 📁 项目结构

```
.
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   ├── auth.py        # 认证接口
│   │   │   ├── datasets.py    # 数据集接口
│   │   │   ├── records.py     # 记录接口
│   │   │   └── analytics.py   # 分析接口
│   │   ├── core/              # 核心功能
│   │   │   ├── security.py    # JWT 安全
│   │   │   ├── deps.py        # 依赖注入
│   │   │   └── middleware.py  # 中间件
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # 业务逻辑
│   │   └── utils/             # 工具函数
│   └── requirements.txt
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── pages/             # 页面组件
│   │   ├── components/        # 通用组件
│   │   ├── services/          # API 服务
│   │   ├── store/             # 状态管理
│   │   └── types/             # TypeScript 类型
│   └── package.json
└── data/                       # 数据存储目录
    ├── app.db                  # SQLite 数据库
    ├── users/                  # 用户数据
    └── uploads/                # 上传文件
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 2. 后端启动

```bash
# 进入项目根目录
cd /path/to/project

# 安装 Python 依赖
pip install -r backend/requirements.txt

# 启动后端服务
python app.py
# 或
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在 http://localhost:8000

### 3. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev
```

前端开发服务器将运行在 http://localhost:5173

### 4. 构建生产版本

```bash
# 构建前端
cd frontend
npm run build

# 前端构建产物会输出到 frontend/dist
# 后端会自动提供前端静态文件服务
```

构建完成后，直接访问 http://localhost:8000 即可使用完整应用。

## 📝 API 文档

启动后端后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 🔑 主要功能

### 1. 用户认证

- 注册新用户
- 登录获取 JWT Token
- Token 自动续期（7天有效期）

### 2. 数据集管理

- 创建/编辑/删除数据集
- 支持多种数据源类型（微博、抖音、手动录入、文件上传）
- 文件上传支持 CSV/Excel

### 3. 数据记录

- 单条记录添加
- 批量导入
- 自动情感分析
- 情感得分计算（0-1）

### 4. 数据分析

- 情感分布统计
- 时间序列趋势
- 关键词提取
- 可视化图表

## 🎨 UI 特性

- 🌈 渐变色设计
- 💫 流畅动画效果
- 📱 响应式布局
- 🎯 直观的用户体验
- 🔔 消息提示反馈

## 🔒 安全特性

- JWT Token 认证
- 密码 bcrypt 加密
- 数据隔离（用户只能访问自己的数据）
- CORS 配置
- SQL 注入防护（ORM）

## 📊 数据库设计

### Users 表
- 用户信息
- 密码哈希
- 角色权限

### DataSets 表
- 数据集信息
- 关联用户
- 记录统计

### DataRecords 表
- 数据记录
- 情感分析结果
- 元数据

### ActivityLogs 表
- 用户操作日志
- 审计跟踪

## 🔧 配置

在项目根目录创建 `.env` 文件：

```env
# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=sqlite:///./data/app.db

# File Storage
DATA_DIR=./data
USER_DATA_DIR=./data/users
UPLOAD_DIR=./data/uploads

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8000"]

# API Keys (Optional)
ZHIPU_API_KEY=
SILICONFLOW_API_KEY=
```

## 🐛 故障排除

### 后端问题

1. **端口被占用**
   ```bash
   # 修改端口
   uvicorn backend.app.main:app --port 8001
   ```

2. **数据库锁定**
   ```bash
   # 删除数据库重新初始化
   rm data/app.db
   # 重启后端，自动创建新数据库
   ```

### 前端问题

1. **依赖安装失败**
   ```bash
   # 清除缓存重新安装
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **API 连接失败**
   - 确保后端已启动
   - 检查 vite.config.ts 中的代理配置

## 📈 性能优化

- SQLite WAL 模式提高并发性能
- FastAPI 异步处理
- 前端代码分割
- 图片懒加载
- API 响应缓存

## 🚦 开发规范

- 使用 TypeScript 确保类型安全
- Pydantic 进行数据验证
- RESTful API 设计
- 统一错误处理
- 代码注释和文档

## 📚 后续计划

- [ ] WebSocket 实时推送
- [ ] Redis 缓存
- [ ] Celery 异步任务队列
- [ ] PostgreSQL 迁移（大规模部署）
- [ ] Docker 容器化
- [ ] 微博/抖音爬虫集成
- [ ] 词云可视化
- [ ] Excel 导出
- [ ] 数据备份/恢复

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题，请提交 Issue 或联系开发团队。
