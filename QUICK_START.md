# 🚀 快速启动指南

## 简介

数据智能分析平台 v2.0 - 多用户社交媒体数据分析系统

## 跨平台启动方式

### 方式一：Python启动器（推荐）

**所有平台通用**

```bash
python launcher.py
# 或
python3 launcher.py
```

首次运行会自动：
- 创建虚拟环境
- 安装依赖
- 初始化数据库
- 创建必要目录

### 方式二：脚本启动

**Windows:**
```cmd
start.bat
```

**Linux/macOS:**
```bash
./start.sh
# 或
bash start.sh
```

### 方式三：命令行参数

```bash
# 初始化设置
python launcher.py setup

# 启动服务器
python launcher.py start

# 运行测试
python launcher.py test

# 检查状态
python launcher.py status
```

## 系统要求

### 必需
- **Python**: 3.8 或更高版本
- **磁盘空间**: 至少 500MB
- **内存**: 建议 2GB 以上

### 检查Python版本

```bash
python --version
# 或
python3 --version
```

如果未安装Python，请访问 https://www.python.org/ 下载安装。

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd data-analysis-system
```

### 2. 运行启动器

```bash
python launcher.py
```

启动器会提示您完成初始设置。

### 3. 配置环境变量（可选）

编辑 `.env` 文件，配置：

```env
# 应用配置
SECRET_KEY=your-secret-key-here
DEBUG=True

# AI服务（可选）
SILICONFLOW_API_KEY=your-api-key
ZHIPU_API_KEY=your-api-key
```

### 4. 访问应用

打开浏览器访问：

**应用主页**: http://localhost:8000  
**API文档**: http://localhost:8000/api/docs  
**管理后台**: http://localhost:8000/api/redoc

## 默认账户

首次运行后，可以创建管理员账户：

```bash
python init_admin.py
```

默认账户信息：
- **用户名**: admin
- **密码**: admin123
- **角色**: 管理员

⚠️ **请在首次登录后立即修改密码！**

## 功能特点

✅ **多用户系统** - 完整的注册、登录、权限管理  
✅ **数据隔离** - 每个用户拥有独立的数据空间  
✅ **微博爬虫** - 自动采集微博数据  
✅ **情感分析** - AI自动分析情感倾向  
✅ **词云生成** - 可视化关键词分布  
✅ **AI报告** - 自动生成分析报告  
✅ **数据导出** - CSV格式导出  
✅ **实时分析** - 实时统计和趋势分析  

## 常见问题

### Q: 启动时提示端口被占用

**A**: 修改端口号
```bash
# 在 app.py 中修改
uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8001)
```

### Q: 依赖安装失败

**A**: 尝试使用国内镜像
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: SQLite数据库锁定

**A**: 系统已启用WAL模式优化并发，如仍出现请重启应用

### Q: 前端无法加载

**A**: 确保 `frontend/dist` 目录存在，或从浏览器直接访问 `/api/docs` 测试后端

## 平台兼容性

### Windows

✅ Windows 10/11  
✅ Windows Server 2019+  
✅ 支持 PowerShell 和 CMD

### macOS

✅ macOS 10.15+  
✅ Apple Silicon (M1/M2) 原生支持  
✅ Intel 处理器支持

### Linux

✅ Ubuntu 18.04+  
✅ Debian 10+  
✅ CentOS 7+  
✅ Fedora  
✅ Arch Linux

## 开发模式

启动开发服务器（自动重载）：

```bash
cd /home/engine/project
python app.py
```

或使用uvicorn直接启动：

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## 生产部署

### 使用Gunicorn（推荐）

```bash
gunicorn backend.app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### 使用Docker

```bash
# 构建镜像
docker build -t data-analysis-system .

# 运行容器
docker run -d -p 8000:8000 data-analysis-system
```

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 更新升级

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
python launcher.py start
```

## 备份数据

重要数据目录：
- `data/` - 数据库和用户数据
- `data/app.db` - SQLite数据库
- `data/users/` - 用户文件
- `.env` - 配置文件

建议定期备份这些目录。

## 卸载

```bash
# 删除虚拟环境
rm -rf venv/

# 删除数据（可选）
rm -rf data/

# 删除日志（可选）
rm -rf logs/
```

## 获取帮助

- **文档**: 查看 `README.md` 和 `ARCHITECTURE.md`
- **API文档**: http://localhost:8000/api/docs
- **问题反馈**: 提交 Issue

## 技术支持

如有问题或建议，请：

1. 查看文档: `README.md`, `NEW_FEATURES.md`, `ARCHITECTURE.md`
2. 运行测试: `python launcher.py test`
3. 检查状态: `python launcher.py status`
4. 提交Issue或联系开发团队

---

**祝使用愉快！🎉**
