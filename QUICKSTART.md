# 🚀 快速启动指南

## 一键启动（推荐）

### 开发环境

```bash
# 1. 准备环境（首次运行）
./start_dev.sh

# 2. 启动后端（终端1）
python app.py

# 3. 启动前端（终端2）
cd frontend && npm run dev
```

访问：http://localhost:5173

### 生产环境

```bash
# 1. 构建前端
./build_prod.sh

# 2. 启动服务器
python app.py
```

访问：http://localhost:8000

## 手动启动

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装 Python 依赖
pip install -r backend/requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 2. 初始化数据库

```bash
# 创建管理员账号
python init_admin.py
```

默认账号：
- 用户名：`admin`
- 密码：`admin123`

### 3. 启动开发服务器

#### 后端（终端1）

```bash
# 方式1：使用 app.py
python app.py

# 方式2：使用 uvicorn
uvicorn backend.app.main:app --reload

# 方式3：指定端口
uvicorn backend.app.main:app --port 8001 --reload
```

后端运行在：http://localhost:8000
API 文档：http://localhost:8000/api/docs

#### 前端（终端2）

```bash
cd frontend
npm run dev
```

前端运行在：http://localhost:5173

### 4. 生产部署

#### 构建前端

```bash
cd frontend
npm run build
cd ..
```

#### 启动生产服务器

```bash
# 方式1：单进程
python app.py

# 方式2：使用 uvicorn
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# 方式3：使用 gunicorn（多进程）
gunicorn backend.app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000
```

## 常见问题

### 1. 端口被占用

```bash
# 查看占用端口的进程
lsof -i :8000  # 后端端口
lsof -i :5173  # 前端端口

# 修改端口
uvicorn backend.app.main:app --port 8001
```

### 2. 数据库锁定

```bash
# 删除数据库重新初始化
rm data/app.db*
python init_admin.py
```

### 3. 前端依赖问题

```bash
# 清除缓存重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 4. Python 依赖问题

```bash
# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

## 目录结构

```
.
├── backend/           # 后端代码（FastAPI）
├── frontend/          # 前端代码（React + TypeScript）
│   └── dist/          # 构建输出（生产环境）
├── data/              # 数据目录
│   ├── app.db         # SQLite 数据库
│   ├── users/         # 用户数据
│   └── uploads/       # 上传文件
├── app.py             # 应用入口
├── init_admin.py      # 初始化管理员
├── start_dev.sh       # 开发环境启动脚本
└── build_prod.sh      # 生产环境构建脚本
```

## 环境变量

复制 `.env.example` 为 `.env` 并根据需要修改：

```bash
cp .env.example .env
```

关键配置：

```env
SECRET_KEY=your-secret-key           # JWT 密钥
ACCESS_TOKEN_EXPIRE_MINUTES=10080    # Token 有效期（7天）
DATABASE_URL=sqlite:///./data/app.db # 数据库路径
```

## 功能验证

### 1. 后端健康检查

```bash
curl http://localhost:8000/api/health
```

应返回：`{"status":"healthy","version":"2.0.0"}`

### 2. 用户注册

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "email": "test@example.com",
    "password": "test123"
  }'
```

### 3. 用户登录

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

## 开发工具

- **API 文档**：http://localhost:8000/api/docs
- **ReDoc 文档**：http://localhost:8000/api/redoc
- **数据库管理**：使用 DB Browser for SQLite

## 技术栈

### 后端
- FastAPI 0.110.2
- SQLAlchemy 2.0.29
- Pydantic 2.10+
- SnowNLP（情感分析）

### 前端
- React 18.3
- TypeScript
- Ant Design 5
- ECharts 5
- Vite 5

## 下一步

1. 修改默认管理员密码
2. 配置 `.env` 文件
3. 创建第一个数据集
4. 上传数据并查看分析结果

## 获取帮助

- 查看完整文档：`README_v2.md`
- API 文档：http://localhost:8000/api/docs
- 提交 Issue：GitHub Issues

---

**祝您使用愉快！** 🎉
