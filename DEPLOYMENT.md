# 🚢 生产环境部署指南

## 目录

1. [部署前准备](#部署前准备)
2. [Docker部署](#docker部署)
3. [手动部署](#手动部署)
4. [云平台部署](#云平台部署)
5. [性能优化](#性能优化)
6. [监控告警](#监控告警)
7. [备份恢复](#备份恢复)

---

## 部署前准备

### 硬件要求

| 规模 | CPU | 内存 | 磁盘 | 带宽 |
|-----|-----|------|------|------|
| 小型（<100用户） | 2核 | 4GB | 20GB | 5Mbps |
| 中型（<1000用户） | 4核 | 8GB | 100GB | 20Mbps |
| 大型（>1000用户） | 8核 | 16GB | 500GB | 100Mbps |

### 软件要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Python**: 3.8+
- **数据库**: SQLite（自带）或 PostgreSQL（推荐大规模）
- **Web服务器**: Nginx（推荐）
- **进程管理**: Supervisor 或 systemd

### 安全检查清单

- [ ] 修改默认SECRET_KEY
- [ ] 禁用DEBUG模式
- [ ] 配置HTTPS证书
- [ ] 配置防火墙规则
- [ ] 设置数据库备份
- [ ] 配置日志轮转
- [ ] 更新默认管理员密码

---

## Docker部署

### 1. 创建Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p data logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"

# Run application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 创建docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - DATABASE_URL=sqlite:///./data/app.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped
```

### 3. 部署命令

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 更新部署
docker-compose pull
docker-compose up -d --force-recreate
```

---

## 手动部署

### Ubuntu/Debian系统

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装依赖
sudo apt install -y python3.10 python3-pip python3-venv nginx supervisor

# 3. 创建应用用户
sudo useradd -m -s /bin/bash dataapp
sudo su - dataapp

# 4. 克隆代码
cd /opt
git clone <repository-url> dataapp
cd dataapp

# 5. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 6. 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 7. 配置环境
cp .env.example .env
# 编辑 .env 文件

# 8. 初始化数据库
python init_admin.py

# 9. 配置Supervisor
sudo nano /etc/supervisor/conf.d/dataapp.conf
```

### Supervisor配置

```ini
[program:dataapp]
command=/opt/dataapp/venv/bin/gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
directory=/opt/dataapp
user=dataapp
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/dataapp/error.log
stdout_logfile=/var/log/dataapp/access.log
environment=PATH="/opt/dataapp/venv/bin"
```

### Nginx配置

```nginx
upstream dataapp {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Upload size
    client_max_body_size 100M;
    
    # Proxy settings
    location / {
        proxy_pass http://dataapp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /assets/ {
        alias /opt/dataapp/frontend/dist/frontend-assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Access log
    access_log /var/log/nginx/dataapp_access.log;
    error_log /var/log/nginx/dataapp_error.log;
}
```

### 启动服务

```bash
# 重载配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动应用
sudo supervisorctl start dataapp

# 重启Nginx
sudo systemctl restart nginx

# 查看状态
sudo supervisorctl status dataapp
```

---

## 云平台部署

### AWS部署

1. **创建EC2实例**（t2.medium或更高）
2. **配置安全组**（开放80, 443, 8000端口）
3. **绑定弹性IP**
4. **配置RDS PostgreSQL**（可选）
5. **使用S3存储文件**（可选）

### 阿里云部署

1. **创建ECS实例**（2核4G或更高）
2. **配置安全组规则**
3. **申请SSL证书**
4. **配置OSS对象存储**（可选）
5. **使用CDN加速静态资源**

### 腾讯云部署

1. **创建CVM实例**
2. **配置防火墙规则**
3. **申请SSL证书**
4. **使用COS对象存储**（可选）

---

## 性能优化

### 数据库优化

```python
# 使用PostgreSQL替代SQLite（大规模场景）
DATABASE_URL = "postgresql://user:pass@localhost/dbname"

# 配置连接池
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### 缓存优化

```python
# 安装Redis
sudo apt install redis-server

# requirements.txt添加
redis==4.6.0
fastapi-cache2==0.2.0

# 配置缓存
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="dataapp:")
```

### Worker进程数

```bash
# 计算公式: (2 * CPU核心数) + 1
# 4核机器
gunicorn -w 9 -k uvicorn.workers.UvicornWorker backend.app.main:app
```

### 静态文件CDN

使用CDN加速静态资源：
- 七牛云
- 阿里云OSS + CDN
- 腾讯云COS + CDN

---

## 监控告警

### 健康检查

```bash
# Endpoint
GET /api/health

# 返回
{
  "status": "healthy",
  "version": "2.0.0"
}
```

### 日志监控

```bash
# 安装日志收集工具
sudo apt install logrotate

# 配置日志轮转
/var/log/dataapp/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 dataapp dataapp
    sharedscripts
    postrotate
        supervisorctl restart dataapp
    endscript
}
```

### 性能监控

推荐工具：
- **Prometheus + Grafana** - 指标监控
- **ELK Stack** - 日志分析
- **Sentry** - 错误追踪

---

## 备份恢复

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/dataapp"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/dataapp/data/app.db $BACKUP_DIR/app_$DATE.db

# 备份用户数据
tar -czf $BACKUP_DIR/userdata_$DATE.tar.gz /opt/dataapp/data/users/

# 备份配置
cp /opt/dataapp/.env $BACKUP_DIR/env_$DATE

# 删除30天前的备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 定时备份

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/dataapp/backup.sh
```

### 恢复数据

```bash
# 停止服务
sudo supervisorctl stop dataapp

# 恢复数据库
cp /backup/dataapp/app_20240101_020000.db /opt/dataapp/data/app.db

# 恢复用户数据
tar -xzf /backup/dataapp/userdata_20240101_020000.tar.gz -C /

# 启动服务
sudo supervisorctl start dataapp
```

---

## 故障排查

### 常见问题

**1. 服务无法启动**
```bash
# 查看日志
sudo supervisorctl tail -f dataapp stderr

# 检查端口占用
sudo lsof -i :8000

# 测试配置
source venv/bin/activate
python backend/app/main.py
```

**2. 数据库锁定**
```bash
# 检查WAL文件
ls -lh data/app.db-*

# 强制checkpoint
sqlite3 data/app.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

**3. 内存不足**
```bash
# 检查内存使用
free -h

# 添加swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 安全加固

### 防火墙配置

```bash
# UFW配置
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### fail2ban配置

```bash
# 安装
sudo apt install fail2ban

# 配置
sudo nano /etc/fail2ban/jail.local

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 3600
```

### 定期更新

```bash
# 系统更新
sudo apt update && sudo apt upgrade -y

# Python依赖更新
pip install -r requirements.txt --upgrade

# 安全补丁
sudo apt install unattended-upgrades
```

---

## 生产环境检查清单

部署前确认：

- [ ] 配置HTTPS证书
- [ ] 修改SECRET_KEY
- [ ] 关闭DEBUG模式
- [ ] 配置防火墙
- [ ] 设置自动备份
- [ ] 配置日志轮转
- [ ] 设置监控告警
- [ ] 更新默认密码
- [ ] 测试性能负载
- [ ] 配置错误追踪
- [ ] 准备回滚方案

---

**部署成功后，记得测试所有功能！🎉**
