# 前端项目文档 (Frontend)

本项目基于 React + Vite + TypeScript 构建，采用 Claude 风格的现代化设计系统。

## 🛠 技术栈
- **核心框架**: React 18, Vite
- **语言**: TypeScript
- **路由**: React Router v6
- **状态管理**: Context API (Auth), Hooks
- **样式**: CSS Modules + Vanilla CSS Variables (Claude Design System)
- **图标**: Lucide React
- **HTTP客户端**: Axios

## 🎨 设计系统
我们实现了一套 "Warm Knowledge" (温暖知识) 风格的设计系统，灵感来源于 Claude AI。
核心变量定义在 `src/index.css` 中：
- 背景色：`#F5F5F3` (Warm Grey)
- 主色调：`#D96C4F` (Burnt Orange)
- 字体：`Merriweather` (标题) + `Inter` (正文)

## 🚀 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```
访问 http://localhost:5173

### 3. 构建生产版本
```bash
npm run build
```

### 4. 启动桌面版调试
```bash
npm run tauri:dev
```

### 5. 构建桌面版
```bash
npm run tauri:build:backend
npm run tauri:build
```

## 📁 目录结构
```
src/
├── assets/         # 静态资源
├── components/     # 组件
│   ├── common/     # 通用组件 (Button, Card, Input...)
│   ├── layout/     # 布局组件 (Sidebar, Header...)
│   └── charts/     # 图表组件
├── context/        # 全局状态 (AuthContext)
├── hooks/          # 自定义 Hooks
├── pages/          # 页面组件 (Dashboard, Login...)
├── services/       # API 服务
├── types/          # TypeScript 类型定义
├── App.tsx         # 路由配置
└── main.tsx        # 入口文件
```

## 🔗 后端集成

- Web 开发环境：Vite 代理将 `/api` 转发到 `http://localhost:8000`
- Tauri 桌面环境：前端会在运行时读取 Rust 注入的本地后端地址

桌面版不要求用户单独安装前后端依赖，后端由桌面壳自动拉起。

## 📝 开发规范
- 使用 **CSS Modules** (`*.module.css`) 进行样式隔离。
- 优先使用 `src/index.css` 中定义的 CSS 变量。
- 组件命名使用 PascalCase。
- 所有 API 请求通过 `services/api.ts` 发起。
