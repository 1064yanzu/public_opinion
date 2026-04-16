# 部署文档

本文档说明如何将 React + FastAPI 舆情分析系统部署到生产环境。

---

## 环境要求

### 服务器配置

- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / macOS
- **Python**: 3.10+
- **Node.js**: 18+
- **RAM**: 至少 4GB
- **磁盘**: 至少 20GB 可用空间

### 软件依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# 或
sudo yum update -y  # CentOS/RHEL

# 安装基础工具
sudo apt install -y git curl wget build-essential

# 安装 Python
sudo apt install -y python3.10 python3.10-venv python3-pip

# 安装 Node.js（使用 nvm）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# 安装 Nginx
sudo apt install -y nginx

# 安装 Supervisor（进程管理）
sudo apt install -y supervisor
```

---

## 后端部署

### 1. 准备项目

```bash
# 克隆项目
cd /var/www/
git clone <项目地址> public_opinion
cd public_opinion/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 安装生产服务器
pip install gunicorn
```

### 2. 配置环境变量

```bash
# 创建生产环境配置
cp .env.example .env
nano .env
```

**生产环境 .env 示例**：
```bash
# 应用配置
APP_NAME=舆情分析系统
DEBUG=False

# 安全配置
SECRET_KEY=your-very-secure-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS 配置（生产域名）
ALLOWED_ORIGINS=["https://your-domain.com", "https://www.your-domain.com"]

# AI 配置
AI_MODEL_TYPE=zhipuai
AI_API_KEY=your-api-key-here
AI_BASE_URL=
AI_MODEL_ID=

# 性能配置
ENABLE_CACHE=True
CACHE_DURATION=300
MAX_WORKERS=4

# 数据路径
DATA_DIR=../data
STATIC_DIR=../static
```

### 3. 配置 Gunicorn

创建 `gunicorn_conf.py`：

```python
# backend/gunicorn_conf.py
import multiprocessing

# 绑定地址和端口
bind = "127.0.0.1:8000"

# Worker 进程数（推荐 CPU 核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# Worker 类型（异步）
worker_class = "uvicorn.workers.UvicornWorker"

# 超时时间
timeout = 120

# 日志
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# 进程名称
proc_name = "public_opinion_api"

# 守护进程（使用 Supervisor 时设为 False）
daemon = False
```

创建日志目录：
```bash
sudo mkdir -p /var/log/gunicorn
sudo chown -R $USER:$USER /var/log/gunicorn
```

### 4. 配置 Supervisor

创建配置文件：
```bash
sudo nano /etc/supervisor/conf.d/public_opinion_api.conf
```

内容：
```ini
[program:public_opinion_api]
directory=/var/www/public_opinion/backend
command=/var/www/public_opinion/backend/venv/bin/gunicorn -c gunicorn_conf.py app.main:app
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/public_opinion_api.log
stderr_logfile=/var/log/supervisor/public_opinion_api_err.log
environment=PATH="/var/www/public_opinion/backend/venv/bin"
```

启动服务：
```bash
# 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动服务
sudo supervisorctl start public_opinion_api

# 检查状态
sudo supervisorctl status public_opinion_api
```

### 5. 测试后端

```bash
# 检查服务是否运行
curl http://127.0.0.1:8000/health

# 查看日志
sudo tail -f /var/log/supervisor/public_opinion_api.log
```

---

## 前端部署

### 1. 构建生产版本

```bash
cd /var/www/public_opinion/frontend

# 配置生产环境变量
cp .env.example .env.production
nano .env.production
```

**生产环境 .env.production 示例**：
```bash
VITE_API_URL=https://api.your-domain.com
```

构建：
```bash
# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建产物在 dist/ 目录
ls -la dist/
```

### 2. 配置 Nginx

创建 Nginx 配置文件：
```bash
sudo nano /etc/nginx/sites-available/public_opinion
```

**基础配置**：
```nginx
# 前端配置
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    root /var/www/public_opinion/frontend/dist;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

    # 前端路由（SPA）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# API 文档（可选，仅开发/测试环境）
server {
    listen 80;
    server_name api-docs.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**启用配置**：
```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/public_opinion /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 3. 配置 HTTPS（推荐）

使用 Let's Encrypt 免费 SSL 证书：

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书并自动配置 Nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期（Certbot 会自动设置 cron job）
sudo certbot renew --dry-run
```

Certbot 会自动修改 Nginx 配置，添加 SSL 相关设置。

---

## 数据迁移

### 迁移数据文件

```bash
# 复制数据文件到服务器
scp -r data/ user@server:/var/www/public_opinion/
scp -r static/content/ user@server:/var/www/public_opinion/static/

# 设置权限
sudo chown -R www-data:www-data /var/www/public_opinion/data
sudo chown -R www-data:www-data /var/www/public_opinion/static
```

### 迁移配置文件

```bash
# 复制配置文件
scp config/* user@server:/var/www/public_opinion/config/
```

---

## 监控和日志

### 应用日志

```bash
# 后端日志
sudo tail -f /var/log/supervisor/public_opinion_api.log
sudo tail -f /var/log/gunicorn/access.log
sudo tail -f /var/log/gunicorn/error.log

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 系统监控

```bash
# 查看进程
ps aux | grep gunicorn
ps aux | grep nginx

# 查看端口
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep 80

# 系统资源
htop
df -h
free -h
```

### 性能监控（可选）

安装监控工具：
```bash
# 安装 PM2（可选，Node.js 应用监控）
npm install -g pm2

# 使用 PM2 运行前端（如果不用 Nginx 静态托管）
pm2 serve dist/ 3000 --name public_opinion_frontend
```

---

## 维护操作

### 更新代码

```bash
# 拉取最新代码
cd /var/www/public_opinion
git pull origin main

# 更新后端
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart public_opinion_api

# 更新前端
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

### 备份

**创建备份脚本**：
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/public_opinion"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据
tar -czf $BACKUP_DIR/data_$TIMESTAMP.tar.gz /var/www/public_opinion/data
tar -czf $BACKUP_DIR/static_$TIMESTAMP.tar.gz /var/www/public_opinion/static/content
tar -czf $BACKUP_DIR/config_$TIMESTAMP.tar.gz /var/www/public_opinion/backend/.env /var/www/public_opinion/config

# 删除 30 天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "备份完成: $TIMESTAMP"
```

**设置定时备份**：
```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点执行备份
0 2 * * * /path/to/backup.sh
```

### 回滚

```bash
# 回滚代码
git log --oneline  # 查看提交历史
git reset --hard <commit-hash>

# 重启服务
sudo supervisorctl restart public_opinion_api
sudo systemctl reload nginx
```

---

## 故障排查

### 后端无法启动

1. **检查日志**：
```bash
sudo tail -f /var/log/supervisor/public_opinion_api_err.log
```

2. **检查环境变量**：
```bash
cd /var/www/public_opinion/backend
cat .env
```

3. **测试配置**：
```bash
source venv/bin/activate
python -c "from app.config import settings; print(settings)"
```

### 前端页面空白

1. **检查 Nginx 配置**：
```bash
sudo nginx -t
```

2. **检查静态文件**：
```bash
ls -la /var/www/public_opinion/frontend/dist
```

3. **查看浏览器控制台错误**

### API 请求失败

1. **检查后端服务**：
```bash
curl http://127.0.0.1:8000/health
```

2. **检查 Nginx 反向代理**：
```bash
sudo tail -f /var/log/nginx/error.log
```

3. **检查 CORS 配置**：
确保 `settings.ALLOWED_ORIGINS` 包含前端域名

---

## 安全建议

1. **使用 HTTPS**：强制所有流量使用 SSL
2. **防火墙配置**：
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

3. **定期更新**：
```bash
sudo apt update && sudo apt upgrade -y
```

4. **限制文件权限**：
```bash
sudo chmod 600 /var/www/public_opinion/backend/.env
```

5. **隐藏敏感信息**：
   - 不要在 Git 仓库中提交 `.env` 文件
   - 使用强密码和密钥
   - 定期轮换 API 密钥

---

## 性能优化

### Nginx 优化

```nginx
# 在 /etc/nginx/nginx.conf 中添加
worker_processes auto;
worker_connections 1024;

# 启用 HTTP/2
listen 443 ssl http2;

# 缓存配置
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
```

### 数据库优化（如使用数据库）

- 添加索引
- 使用连接池
- 配置查询缓存

### 应用优化

- 启用 Redis 缓存
- 使用 CDN 加速静态资源
- 优化图片和资源大小

---

## 扩展部署

### Docker 部署（可选）

**后端 Dockerfile**：
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile**：
```dockerfile
FROM node:18-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

**docker-compose.yml**：
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./data:/app/data
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

---

## 参考资源

- [Nginx 官方文档](https://nginx.org/en/docs/)
- [Supervisor 文档](http://supervisord.org/)
- [Gunicorn 文档](https://docs.gunicorn.org/)
- [Let's Encrypt](https://letsencrypt.org/)
