# 更新日志

## [2.0.0] - 2024-10-17

### 🎉 重大重构

完全重构项目，从 Flask 单体应用升级为 FastAPI + React 前后端分离架构。

### ✨ 新增

#### 前端
- ✅ **React 18.3 + TypeScript**：现代化前端框架，类型安全
- ✅ **Ant Design 5**：企业级 UI 组件库
- ✅ **Vite 5**：极速构建工具
- ✅ **Zustand 状态管理**：轻量级状态管理，支持持久化
- ✅ **ECharts 5**：数据可视化图表
- ✅ **Axios**：HTTP 客户端，自动 Token 注入
- ✅ **响应式设计**：适配移动端和桌面端
- ✅ **渐变色 UI**：紫色系现代化设计
- ✅ **流畅动画**：过渡效果和悬浮效果

#### 后端
- ✅ **FastAPI 0.110.2**：高性能异步 Web 框架
- ✅ **Pydantic 2.10+**：自动数据验证和序列化
- ✅ **JWT 认证**：无状态认证，7 天有效期
- ✅ **自动 API 文档**：Swagger UI 和 ReDoc
- ✅ **异步处理**：提高并发性能
- ✅ **后台任务**：批量导入异步处理
- ✅ **依赖注入**：解耦代码，易于测试
- ✅ **类型提示**：Python 类型注解

#### 功能
- ✅ **用户注册登录**：完整的用户认证系统
- ✅ **数据集管理**：创建、编辑、删除数据集
- ✅ **多种导入方式**：手动、批量、文件上传（CSV/Excel）
- ✅ **情感分析**：基于 SnowNLP 的中文情感分析
- ✅ **数据可视化**：情感分布、时间趋势、关键词统计
- ✅ **数据隔离**：用户数据完全隔离
- ✅ **活动日志**：记录用户操作

### 🔧 优化

#### 性能
- ✅ SQLite WAL 模式：支持并发读写
- ✅ 数据库连接池：优化连接管理
- ✅ 索引优化：加快查询速度
- ✅ 代码分割：前端按需加载

#### 安全
- ✅ JWT Token 认证
- ✅ bcrypt 密码加密
- ✅ CORS 配置
- ✅ SQL 注入防护（ORM）
- ✅ 请求数据验证

#### 代码质量
- ✅ TypeScript 类型安全
- ✅ Python 类型注解
- ✅ 统一代码风格
- ✅ 组件化开发
- ✅ 模块化设计

### 📁 新增文件

- `QUICKSTART.md` - 快速启动指南
- `README_v2.md` - 完整项目文档
- `REFACTORING_SUMMARY.md` - 重构总结
- `CHANGELOG.md` - 更新日志（本文件）
- `.env.example` - 环境变量配置示例
- `start_dev.sh` - 开发环境启动脚本
- `build_prod.sh` - 生产环境构建脚本

### 🗂️ 目录重组

```
backend/app/
├── api/           # API 路由
├── core/          # 核心功能
├── models/        # 数据模型
├── schemas/       # 数据验证
├── services/      # 业务逻辑
└── utils/         # 工具函数

frontend/src/
├── pages/         # 页面组件
├── components/    # 通用组件
├── services/      # API 服务
├── store/         # 状态管理
└── types/         # 类型定义
```

### 🔄 API 变更

#### 新增端点
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录（返回 Token + User）
- `GET /api/auth/me` - 获取当前用户
- `GET /api/datasets/` - 列出数据集
- `POST /api/datasets/` - 创建数据集
- `PUT /api/datasets/{id}` - 更新数据集
- `DELETE /api/datasets/{id}` - 删除数据集
- `POST /api/datasets/{id}/upload` - 上传文件
- `GET /api/datasets/{id}/records` - 获取记录列表
- `POST /api/records/` - 创建单条记录
- `POST /api/records/bulk` - 批量创建记录
- `DELETE /api/records/{id}` - 删除记录
- `GET /api/analytics/{dataset_id}` - 获取分析报告
- `GET /api/health` - 健康检查

#### 响应格式
- 统一使用 Pydantic Schemas
- 错误响应标准化
- 包含详细的验证错误信息

### 🔐 安全改进

- 密码使用 bcrypt 加密
- JWT Token 认证，7 天有效期
- 所有 API 需要认证（除注册/登录）
- 用户数据完全隔离
- CORS 安全配置
- 防止 SQL 注入

### 📊 数据库变更

#### 保持兼容
- User 表结构保持
- DataSet 表结构保持
- DataRecord 表结构保持
- ActivityLog 表结构保持

#### 优化
- 添加 WAL 模式
- 优化索引
- 添加外键约束

### 🎨 UI/UX 改进

- 全新的视觉设计（紫色渐变主题）
- 响应式布局
- 流畅的动画效果
- 友好的错误提示
- 即时的操作反馈
- 统一的操作入口

### 📚 文档完善

- 完整的 API 文档（自动生成）
- 快速启动指南
- 详细的项目文档
- 重构总结
- 环境变量配置说明

### 🚀 部署改进

- 一键启动脚本
- 生产构建脚本
- 环境变量配置
- Docker 支持（计划中）

### 🐛 修复

- 修复并发读写问题（WAL 模式）
- 修复数据隔离问题
- 修复密码加密问题
- 修复 Token 过期处理

### ⚠️ 破坏性变更

#### 前端
- 不再使用 Flask 模板
- 需要构建前端（开发环境可选）
- 需要配置 CORS

#### 后端
- API 路径变更（添加 `/api` 前缀）
- 认证方式变更（从 Session 到 JWT）
- 响应格式变更（标准化 JSON）

### 📦 依赖变更

#### 新增
- fastapi
- pydantic
- pydantic-settings
- python-jose
- passlib
- email-validator

#### 移除
- flask
- flask-login
- flask-session

### 🔮 未来计划

- [ ] WebSocket 实时推送
- [ ] Redis 缓存
- [ ] Celery 任务队列
- [ ] PostgreSQL 支持
- [ ] Docker 容器化
- [ ] 单元测试
- [ ] 集成测试
- [ ] CI/CD 流程
- [ ] 微博爬虫集成
- [ ] 抖音爬虫集成
- [ ] 词云可视化增强
- [ ] Excel 导出
- [ ] 数据备份恢复

## [1.0.0] - 历史版本

### 特性
- Flask 单体应用
- Jinja2 模板引擎
- jQuery 前端
- Session 认证
- SQLite 数据库
- SnowNLP 情感分析
- 基础数据可视化

---

**完整更新内容请查看 Git 提交历史**
