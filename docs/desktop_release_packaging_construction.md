# 桌面端发布打包施工文档

## 文档信息

- 任务日期：2026-04-16
- 任务目标：清理误入版本控制的本地构建产物，并打通本地 mac 打包与远端 Windows 安装包发布链路
- 影响范围：`.gitignore`、桌面后端打包脚本、GitHub Actions 发布工作流

---

## 问题背景

本轮有两个直接问题：

1. 本地执行桌面构建后，`frontend/src-tauri/resources/backend/` 产物出现在 `git status`
2. `frontend/tsconfig.tsbuildinfo` 作为构建缓存被长期跟踪，持续污染工作区

同时，远端 Windows 发布链路还存在两个潜在风险：

- `release.yml` 使用 `Node 18`，与当前前端依赖栈不匹配，容易在 Vite/Tauri 构建阶段失败
- 工作流无论字体文件是否存在都强行传 `--add-data`，会把 PyInstaller 构建变成脆弱点

---

## 本次实施内容

### 1. 清理本地构建产物的版本控制污染

- 文件：
  - `.gitignore`
- 处理：
  - 增加 `*.tsbuildinfo`
  - 明确忽略 `frontend/src-tauri/resources/backend/**`
  - 忽略 `backend/.pyinstaller/`

### 2. 加固桌面后端本地打包脚本

- 文件：
  - `backend/scripts/build_desktop_backend.sh`
- 处理：
  - 将字体资源参数改为“仅当文件存在时才追加 `--add-data`”
  - 避免因为可选字体资源缺失导致 mac 本地 sidecar 构建直接失败

### 3. 加固 GitHub Actions Windows 发布流程

- 文件：
  - `.github/workflows/release.yml`
- 处理：
  - 将 Node 版本升级到 `20`
  - `npm install` 改为 `npm ci`
  - cache 依赖文件改为 `frontend/package-lock.json`
  - 增加 `pip` 升级步骤
  - 将字体资源参数改为条件拼接，避免 PyInstaller 因缺字库报错

---

## 本次验证计划

### 本地 mac

- 执行：`cd frontend && npm run tauri:build`
- 目标：产出 mac 桌面安装包/应用包，并验证 sidecar 打包链路可用

### 远端 Windows

- 条件：代码推送到 GitHub 后，通过 tag 或 `workflow_dispatch` 触发
- 产物：`frontend/src-tauri/target/x86_64-pc-windows-msvc/release/bundle/nsis/*.exe`

---

## 当前限制说明

- 当前环境没有 `gh` CLI，无法直接在本地调用 GitHub API 触发远端 workflow
- 在本地改动尚未 push 前，GitHub 远端也拿不到这些修复，因此远端 exe 打包必须在推送后执行

---

## 第二轮排障补充（2026-04-17）

### 新暴露的问题

在远端 Windows 与本地 mac 打包阶段，Tauri 构建脚本都在处理 `resources/backend` 时失败：

- Windows：`build-script-build` 在枚举 `resources/backend/public_opinion_backend/_internal/...` 超大资源树后失败
- mac：`Not a directory (os error 20)`，表现为 Tauri 在递归资源时撞到 `public_opinion_backend/public_opinion_backend` 同名文件/目录结构

### 根因结论

根因不是业务代码，而是把 `PyInstaller --onedir` 产出的整个 sidecar 目录作为 Tauri `bundle.resources` 递归打包。该目录：

- 文件数量极多
- 层级很深
- 还包含“目录名与可执行文件名相同”的结构

这会让 Tauri 在不同平台上都表现得很脆弱。

### 修复方案

- 将桌面后端 sidecar 从 `PyInstaller --onedir` 改回 `--onefile`
- 这样 Tauri 只需要携带单个 `public_opinion_backend(.exe)`，不再递归打包庞大的 `_internal` 资源树
- 该方案会带来更慢的首次启动，但当前桌面端已经有更长的启动等待与日志排障闭环，能承受这个代价
