# 开发指南

## 环境要求

### 后端
- Python 3.10+
- pip 包管理器

### 前端
- Node.js 18+
- npm 9+

---

## 快速开始

### 克隆项目

```bash
git clone <项目地址>
cd public_opinion
```

### 后端开发环境

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://localhost:8000/docs

### 前端开发环境

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动开发服务器
npm run dev
```

访问应用：http://localhost:5173

---

## 项目结构

### 后端结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── dependencies.py      # 依赖注入
│   ├── routers/             # API 路由
│   │   ├── auth.py          # 认证相关
│   │   ├── spider.py        # 爬虫相关
│   │   ├── analysis.py      # 数据分析
│   │   ├── monitor.py       # 系统监控
│   │   └── tasks.py         # 任务管理
│   ├── models/              # 数据模型（Pydantic）（可选）
│   └── utils/               # 工具函数（可选）
├── spiders/                 # 爬虫模块
├── model/                   # NLP 模块
├── utils/                   # 工具函数
├── requirements.txt         # Python 依赖
└── .env                     # 环境变量
```

### 前端结构

```
frontend/
├── public/                  # 静态资源
├── src/
│   ├── main.tsx            # 入口文件
│   ├── App.tsx             # 根组件
│   ├── components/         # 通用组件
│   │   ├── Layout/         # 布局组件
│   │   ├── DataTable/      # 数据表格
│   │   └── Charts/         # 图表组件
│   ├── pages/              # 页面组件
│   │   ├── Home/           # 主页
│   │   ├── Login/          # 登录
│   │   ├── Spider/         # 爬虫设置
│   │   ├── Analysis/       # 数据分析
│   │   └── Monitor/        # 系统监控
│   ├── stores/             # 状态管理（Zustand）
│   │   ├── authStore.ts    # 认证状态
│   │   ├── spiderStore.ts  # 爬虫状态
│   │   └── ...
│   ├── services/           # API 服务
│   │   ├── api.ts          # Axios 配置
│   │   ├── auth.ts         # 认证服务
│   │   └── spider.ts       # 爬虫服务
│   ├── hooks/              # 自定义 Hooks
│   ├── utils/              # 工具函数
│   └── styles/             # 样式文件
├── package.json
├── vite.config.ts          # Vite 配置
├── tsconfig.json           # TypeScript 配置
└── .env                    # 环境变量
```

---

## 开发规范

### 代码风格

#### Python（后端）

遵循 PEP 8 规范：

```python
# 函数命名：小写下划线
def get_user_info():
    pass

# 类命名：大驼峰
class UserService:
    pass

# 常量：大写下划线
MAX_PAGE_SIZE = 50

# 私有变量：单下划线前缀
def _internal_function():
    pass
```

#### TypeScript（前端）

遵循 Airbnb 规范：

```typescript
// 组件命名：大驼峰
function UserProfile() {}

// 函数命名：小驼峰
function getUserInfo() {}

// 常量：大写下划线
const MAX_PAGE_SIZE = 50;

// 类型定义：大驼峰
interface UserInfo {}
type ApiResponse = {};
```

### Git 工作流

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/new-feature

# 创建 Pull Request
```

### 提交信息规范

使用 Conventional Commits：

- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `perf:` 性能优化
- `test:` 测试相关
- `chore:` 构建、配置等

示例：
```
feat: 添加微博爬虫功能
fix: 修复登录失败问题
docs: 更新 API 文档
```

---

## API 开发

### 创建新的 API 端点

1. **定义数据模型**（Pydantic）

```python
# app/routers/example.py
from pydantic import BaseModel

class ExampleRequest(BaseModel):
    name: str
    age: int

class ExampleResponse(BaseModel):
    id: int
    message: str
```

2. **创建路由**

```python
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/example", response_model=ExampleResponse)
async def create_example(request: ExampleRequest):
    # 业务逻辑
    if not request.name:
        raise HTTPException(status_code=400, detail="名称不能为空")
    
    return ExampleResponse(
        id=1,
        message=f"Hello, {request.name}!"
    )
```

3. **注册路由**

```python
# app/main.py
from app.routers import example

app.include_router(example.router, prefix="/api/example", tags=["示例"])
```

### API 文档

FastAPI 自动生成 API 文档，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 前端开发

### 创建新页面

1. **创建页面组件**

```typescript
// src/pages/NewPage/index.tsx
import React from 'react';

export default function NewPage() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">新页面</h1>
      {/* 页面内容 */}
    </div>
  );
}
```

2. **添加路由**

```typescript
// src/App.tsx
import NewPage from './pages/NewPage';

<Route path="/new-page" element={<NewPage />} />
```

### 使用状态管理

```typescript
// src/stores/exampleStore.ts
import { create } from 'zustand';

interface ExampleState {
  count: number;
  increment: () => void;
  decrement: () => void;
}

export const useExampleStore = create<ExampleState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
}));

// 在组件中使用
function MyComponent() {
  const { count, increment } = useExampleStore();
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={increment}>Increment</button>
    </div>
  );
}
```

### API 请求

```typescript
// src/services/example.ts
import api from './api';

export const exampleService = {
  getList: async () => {
    return await api.get('/example/list');
  },
  
  create: async (data: any) => {
    return await api.post('/example', data);
  },
};

// 使用 React Query
import { useQuery, useMutation } from '@tanstack/react-query';

function MyComponent() {
  const { data, isLoading } = useQuery({
    queryKey: ['examples'],
    queryFn: exampleService.getList,
  });

  const mutation = useMutation({
    mutationFn: exampleService.create,
    onSuccess: () => {
      // 成功后的操作
    },
  });

  return (
    <div>
      {isLoading ? '加载中...' : JSON.stringify(data)}
      <button onClick={() => mutation.mutate({ name: 'Test' })}>
        创建
      </button>
    </div>
  );
}
```

---

## 测试

### 后端测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试
pytest
```

测试示例：
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "舆情分析系统 API"
```

### 前端测试

```bash
# 安装测试依赖
npm install -D vitest @testing-library/react @testing-library/jest-dom

# 运行测试
npm run test
```

测试示例：
```typescript
// src/pages/Home/Home.test.tsx
import { render, screen } from '@testing-library/react';
import Home from './index';

test('renders home page', () => {
  render(<Home />);
  const heading = screen.getByText(/舆情分析系统/i);
  expect(heading).toBeInTheDocument();
});
```

---

## 调试

### 后端调试

```python
# 使用 logging
import logging

logger = logging.getLogger(__name__)
logger.info("调试信息")
logger.error("错误信息")

# 使用 pdb
import pdb; pdb.set_trace()
```

### 前端调试

```typescript
// 使用 console
console.log('调试信息', data);
console.error('错误信息', error);

// 使用 React DevTools
// Chrome 扩展：React Developer Tools
```

---

## 性能优化

### 后端优化

1. **使用异步函数**
```python
async def get_data():
    # 异步操作
    pass
```

2. **添加缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_function():
    pass
```

3. **数据库查询优化**（如使用数据库）

### 前端优化

1. **使用 React.memo**
```typescript
const MemoizedComponent = React.memo(MyComponent);
```

2. **懒加载**
```typescript
const LazyComponent = React.lazy(() => import('./Component'));
```

3. **代码分割**
```typescript
// Vite 自动处理代码分割
```

---

## 常见问题

### 如何添加新的依赖？

**后端**：
```bash
pip install package-name
pip freeze > requirements.txt
```

**前端**：
```bash
npm install package-name
```

### 如何处理环境变量？

**后端**：在 `.env` 文件中配置，通过 `settings` 访问

**前端**：在 `.env` 文件中配置（前缀 `VITE_`），通过 `import.meta.env` 访问

### 如何部署？

参考 [deployment.md](./deployment.md)

---

## 资源链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Vite 文档](https://vitejs.dev/)
- [TypeScript 文档](https://www.typescriptlang.org/)
- [TanStack Query 文档](https://tanstack.com/query/latest)
