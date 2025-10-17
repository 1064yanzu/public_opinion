# 项目架构设计文档

## 🎯 设计原则

本项目遵循以下设计原则：

1. **模块化解耦** - 各功能模块独立，通过接口交互
2. **高可扩展性** - 支持插件化扩展新功能
3. **数据隔离** - 多用户数据完全隔离
4. **异步并发** - 支持高并发场景
5. **可维护性** - 清晰的代码结构和文档

## 📐 整体架构

```
┌──────────────────────────────────────────────────────┐
│                   Frontend Layer                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  React Components (Single Page App)         │   │
│  │  - Dashboard, DatasetList, Analytics        │   │
│  │  - LocalStorage State Management            │   │
│  │  - Fetch API Client                         │   │
│  └─────────────────────────────────────────────┘   │
└───────────────────┬──────────────────────────────────┘
                    │ HTTP/JSON + SSE
┌───────────────────▼──────────────────────────────────┐
│                 API Layer (FastAPI)                  │
│  ┌─────────────────────────────────────────────┐   │
│  │  RESTful Endpoints:                         │   │
│  │  - /api/auth      - Authentication          │   │
│  │  - /api/datasets  - Dataset Management      │   │
│  │  - /api/records   - Record Operations       │   │
│  │  - /api/analytics - Analytics               │   │
│  │  - /api/spider    - Spider Crawling         │   │
│  │  - /api/ai        - AI Assistant            │   │
│  │  - /api/wordcloud - Wordcloud Gen           │   │
│  └─────────────────────────────────────────────┘   │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────┐
│              Service Layer (业务逻辑)                │
│  ┌──────────────┬──────────────┬─────────────────┐  │
│  │SpiderService │NLPService    │AIService        │  │
│  │WordCloudSvc  │AnalyticsSvc  │BackgroundTasks  │  │
│  └──────────────┴──────────────┴─────────────────┘  │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────┐
│          Data Access Layer (SQLAlchemy ORM)          │
│  ┌──────────────┬──────────────┬─────────────────┐  │
│  │User Model    │Dataset Model │Record Model     │  │
│  │Log Model     │              │                 │  │
│  └──────────────┴──────────────┴─────────────────┘  │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────┐
│              Storage Layer (Persistence)             │
│  ┌─────────────────────────────────────────────┐   │
│  │  SQLite (WAL Mode)                          │   │
│  │  File System (User Data, CSV, Images)      │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## 🔌 模块化设计

### 1. Spider Service (爬虫服务)

**设计模式**: 工厂模式 + 策略模式

```python
# 基础接口
class BaseSpider(ABC):
    @abstractmethod
    def crawl(self, keyword: str, max_pages: int) -> List[Dict]:
        pass
    
    @abstractmethod
    def parse_item(self, item: Dict) -> Optional[Dict]:
        pass

# 具体实现
class WeiboSpider(BaseSpider):
    def crawl(self, keyword, max_pages):
        # 微博特定实现
        pass

class DouyinSpider(BaseSpider):
    def crawl(self, keyword, max_pages):
        # 抖音特定实现
        pass

# 工厂类
class SpiderFactory:
    _spiders = {
        'weibo': WeiboSpider,
        'douyin': DouyinSpider,
    }
    
    @classmethod
    def create(cls, source: str) -> BaseSpider:
        spider_class = cls._spiders.get(source)
        if not spider_class:
            raise ValueError(f"Unknown source: {source}")
        return spider_class()
    
    @classmethod
    def register_spider(cls, name: str, spider_class: type):
        """扩展点：注册新的爬虫"""
        cls._spiders[name] = spider_class
```

**扩展方法**：
```python
# 添加新的爬虫源
class XiaohongshuSpider(BaseSpider):
    def crawl(self, keyword, max_pages):
        # 小红书爬虫实现
        pass

# 注册
SpiderFactory.register_spider('xiaohongshu', XiaohongshuSpider)
```

### 2. AI Service (AI服务)

**设计模式**: 策略模式 + 适配器模式

```python
# AI Provider接口
class AIProvider(ABC):
    @abstractmethod
    def chat_completion(self, messages, stream, **kwargs):
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass

# 具体Provider
class SiliconFlowProvider(AIProvider):
    def chat_completion(self, messages, stream, **kwargs):
        # SiliconFlow API调用
        pass

class ZhipuAIProvider(AIProvider):
    def chat_completion(self, messages, stream, **kwargs):
        # ZhipuAI API调用
        pass

# 统一服务
class AIService:
    def __init__(self):
        self.providers = {
            'siliconflow': SiliconFlowProvider(),
            'zhipuai': ZhipuAIProvider(),
        }
    
    def get_provider(self, name: str) -> AIProvider:
        # 获取可用的provider
        pass
    
    def register_provider(self, name: str, provider: AIProvider):
        """扩展点：注册新的AI Provider"""
        self.providers[name] = provider
```

**扩展方法**：
```python
# 添加OpenAI支持
class OpenAIProvider(AIProvider):
    def chat_completion(self, messages, stream, **kwargs):
        # OpenAI API
        pass

# 注册
ai_service = AIService()
ai_service.register_provider('openai', OpenAIProvider())
```

### 3. NLP Service (NLP服务)

**职责**：文本处理和分析
- 情感分析（SnowNLP）
- 关键词提取（jieba）
- 文本清洗
- 分词处理

**扩展点**：
```python
class NLPService:
    def __init__(self):
        self.analyzers = {
            'sentiment': self.analyze_sentiment,
            'keywords': self.extract_keywords,
        }
    
    def register_analyzer(self, name: str, func: callable):
        """扩展点：注册新的分析器"""
        self.analyzers[name] = func
```

### 4. Analytics Service (分析服务)

**职责**：数据统计和分析
- 情绪分布统计
- 趋势分析
- 关键指标计算

**解耦设计**：
- 与数据库层解耦，通过ORM模型交互
- 可独立测试
- 易于扩展新的分析维度

## 🔄 数据流设计

### 1. 爬虫数据流

```
用户触发 → API Endpoint → Spider Service
                                ↓
                          Spider Factory → 具体Spider
                                ↓
                          原始数据 → NLP Service (情感分析)
                                ↓
                          DataRecord → 保存到数据库
                                ↓
                          更新Dataset统计 → 返回结果
```

### 2. AI报告生成流

```
用户请求 → API Endpoint → 验证Dataset权限
                                ↓
                          Analytics Service → 生成分析上下文
                                ↓
                          AI Service → 选择Provider
                                ↓
                          流式生成 → SSE推送给前端
                                ↓
                          前端实时渲染
```

### 3. 词云生成流

```
用户请求 → API Endpoint → 获取Dataset Records
                                ↓
                          WordCloud Service → 文本分词
                                ↓
                          生成词云图像 → Base64编码
                                ↓
                          返回JSON（含图像和词频）
```

## 📦 依赖注入

使用FastAPI的依赖注入系统：

```python
# 数据库会话注入
@router.get("/datasets/")
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 自动获取db和current_user
    pass

# 权限验证注入
def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403)
    return current_user
```

## 🔐 安全设计

### 1. 多用户数据隔离

**数据库层**：
```sql
-- 所有查询自动带user_id过滤
SELECT * FROM datasets WHERE user_id = :current_user_id
```

**API层**：
```python
# 自动验证权限
dataset = db.query(DataSet).filter(
    DataSet.id == dataset_id,
    DataSet.user_id == current_user.id  # 强制用户验证
).first()
```

**文件系统层**：
```python
# 用户数据分目录存储
/data/users/user_1/dataset_1/records.csv
/data/users/user_2/dataset_3/records.csv
```

### 2. JWT认证流程

```
登录 → 验证密码 → 生成JWT Token
                        ↓
                  返回Token给前端
                        ↓
前端保存到LocalStorage → 每次请求带Authorization Header
                        ↓
后端验证Token → 提取user_id → 查询User
                        ↓
                  注入到Endpoint函数
```

## 🚀 性能优化

### 1. 数据库优化

```python
# SQLite WAL模式
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000;  # 64MB cache
PRAGMA busy_timeout=30000;  # 30s

# 索引优化
- user_id索引
- created_at索引
- 复合索引(user_id, created_at)
```

### 2. 异步处理

```python
# 后台任务
@router.post("/spider/crawl")
def start_crawl(background_tasks: BackgroundTasks, ...):
    background_tasks.add_task(crawl_task, ...)
    return {"status": "started"}

# 不阻塞主线程
```

### 3. 流式响应

```python
# AI报告生成
@router.post("/ai/report")
def generate_report(...):
    def generate():
        for chunk in ai_service.generate_report(...):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

## 📈 扩展性设计

### 1. 插件化爬虫

```python
# 第三方开发者可以这样扩展
from backend.app.services.spider_service import BaseSpider, SpiderFactory

class MyCustomSpider(BaseSpider):
    def crawl(self, keyword, max_pages):
        # 自定义实现
        pass

# 注册
SpiderFactory.register_spider('my_source', MyCustomSpider)
```

### 2. 自定义AI Provider

```python
# 支持任意AI服务
from backend.app.services.ai_service import AIProvider, AIService

class MyAIProvider(AIProvider):
    def chat_completion(self, messages, stream, **kwargs):
        # 调用自己的AI API
        pass

# 注册
ai_service.register_provider('my_ai', MyAIProvider())
```

### 3. 新增分析维度

```python
# 扩展分析服务
class CustomAnalyzer:
    def analyze_emotion_depth(self, records):
        # 自定义分析
        pass

# 集成到API
@router.get("/analytics/{dataset_id}/custom")
def custom_analysis(...):
    analyzer = CustomAnalyzer()
    return analyzer.analyze_emotion_depth(records)
```

## 🎨 前端架构

### 组件化设计

```javascript
// 独立组件
- LoginView (认证)
- Dashboard (仪表盘)
- DatasetList (数据集列表)
- RecordsView (记录视图)
- SentimentView (情绪分析)
- WordCloudView (词云)

// 表单组件
- DatasetForm (创建数据集)
- RecordForm (添加记录)
- CrawlForm (爬虫配置)

// 工具组件
- Header (顶栏)
- Modal (弹窗)
- Toast (提示)
```

### 状态管理

```javascript
// 使用localStorage持久化
function usePersistedState(key, defaultValue) {
    const [value, setValue] = useState(() => {
        const stored = localStorage.getItem(key);
        return stored ? JSON.parse(stored) : defaultValue;
    });
    
    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
    }, [key, value]);
    
    return [value, setValue];
}

// 应用
const [token, setToken] = usePersistedState('auth-token', null);
```

## 🧪 测试设计

### 单元测试

```python
# 测试Service层
def test_sentiment_analysis():
    nlp_service = NLPService()
    score, label = nlp_service.analyze_sentiment("这个产品很好")
    assert label == "positive"
    assert score > 0.6

# 测试Spider
def test_weibo_spider():
    spider = WeiboSpider()
    results = spider.crawl("测试", max_pages=1)
    assert isinstance(results, list)
```

### API测试

```python
# 使用FastAPI TestClient
def test_create_dataset(client, auth_token):
    response = client.post(
        "/api/datasets/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试数据集", "source": "manual"}
    )
    assert response.status_code == 200
```

## 📝 配置管理

### 环境变量

```python
# .env文件
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./data/app.db
SILICONFLOW_API_KEY=sk-xxx
ZHIPU_API_KEY=xxx

# 通过pydantic-settings自动加载
class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str
    SILICONFLOW_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
```

## 🔄 版本迁移

### 数据库迁移

```bash
# 使用Alembic
alembic init alembic
alembic revision --autogenerate -m "Add new column"
alembic upgrade head
```

### API版本管理

```python
# 支持多版本API
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")
```

## 📊 监控和日志

### 活动日志

```python
# 自动记录用户操作
log_activity(
    db, user,
    action="create_dataset",
    resource="dataset",
    resource_id=dataset.id,
    details=json.dumps({"name": dataset.name})
)
```

### 性能监控

```python
# 中间件自动记录
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {process_time:.3f}s")
        return response
```

## 🎯 最佳实践

1. **单一职责**: 每个Service只负责一个领域
2. **依赖倒置**: 依赖抽象而非具体实现
3. **开闭原则**: 对扩展开放，对修改关闭
4. **接口隔离**: 小而精的接口定义
5. **里氏替换**: 子类可以替换父类

## 🔮 未来扩展方向

1. **插件市场**: 支持第三方插件上传和分享
2. **自定义数据源**: 允许用户配置API端点
3. **工作流引擎**: 可视化配置数据处理流程
4. **多租户支持**: 企业级多组织管理
5. **微服务拆分**: 爬虫、AI、分析独立服务

---

**设计原则总结**:
- ✅ 高内聚低耦合
- ✅ 面向接口编程
- ✅ 依赖注入
- ✅ 工厂模式
- ✅ 策略模式
- ✅ 适配器模式

这样的架构设计确保了系统的**可扩展性**、**可维护性**和**可测试性**。
