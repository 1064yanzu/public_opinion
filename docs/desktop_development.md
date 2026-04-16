# Tauri 桌面开发指南

本文档说明当前仓库的桌面版开发与打包流程。

## 当前桌面架构

- 前端：`React + Vite + TypeScript`
- 桌面壳：`Tauri v2`
- 内置后端：`Python FastAPI`
- 本地存储：`SQLite + 本地文件目录`

桌面版运行时由 `Tauri` 启动内置 Python 后端，再由前端通过本地 HTTP 地址访问 API。

---

## 目录结构

```text
frontend/
├── src-tauri/                  # Tauri Rust 壳层
│   ├── src/main.rs             # 桌面命令与后端子进程管理
│   ├── tauri.conf.json         # Tauri 配置
│   └── capabilities/           # 权限能力配置
├── src/services/runtime.ts     # Web / Desktop 运行时抽象
└── package.json                # tauri:dev / tauri:build 脚本

backend/
├── run_desktop.py              # 桌面版后端启动入口
└── scripts/build_desktop_backend.sh
                               # PyInstaller 后端打包脚本
```

---

## 本地开发

### 1. 准备依赖

```bash
# 根目录 Python 依赖
source .venv/bin/activate
pip install -r backend/requirements.txt

# 前端依赖
cd frontend
npm install
```

### 2. 启动 Web 前端调试

```bash
cd frontend
npm run dev
```

### 3. 启动桌面调试

```bash
cd frontend
npm run tauri:dev
```

`tauri:dev` 会：

1. 启动 Vite 前端
2. 启动桌面壳
3. 由 Rust 侧自动拉起内置 Python FastAPI

---

## 后端桌面二进制打包

桌面生产包不再依赖用户本机安装 Python。  
当前通过 `PyInstaller` 将 `backend/run_desktop.py` 打成可执行文件，并放入：

```text
frontend/src-tauri/resources/backend/
```

执行命令：

```bash
cd frontend
npm run tauri:build:backend
```

---

## 桌面生产构建

建议顺序：

```bash
cd frontend
npm run tauri:build:backend
npm run tauri:build
```

说明：

- 第一步先生成可分发的 Python 后端二进制
- 第二步再由 Tauri 将前端和后端一起打包为桌面应用

---

## 桌面配置闭环

桌面版新增了系统配置能力，前端设置页可直接配置：

- AI 服务类型
- AI API Key / Base URL / Model ID
- 抖音 Cookie
- 数据目录
- 报告目录
- 词云目录
- 数据库文件路径
- 日志目录

对应接口：

- `GET /api/system/config`
- `PUT /api/system/config`
- `GET /api/system/runtime`

---

## 当前限制

1. 首次 `cargo check` / `tauri build` 会下载较多 Rust crates
2. 如果磁盘空间不足，桌面构建会失败
3. 若修改数据库路径、静态目录、报告目录等路径配置，需要重启内置后端
