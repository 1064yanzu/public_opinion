# 新增功能说明

## 📋 目录

1. [保留的原有功能](#保留的原有功能)
2. [新增功能](#新增功能)
3. [架构优化](#架构优化)
4. [API端点说明](#api端点说明)
5. [使用示例](#使用示例)

---

## 保留的原有功能

### ✅ 微博爬虫

**原有路径**: `spiders/articles_spider.py`  
**新架构**: `backend/app/services/spider_service.py` (WeiboSpider)

```python
# 保留全部功能：
- 关键词搜索
- 多页爬取
- 数据解析（作者、内容、时间、点赞数、转发数、评论数）
- 去重机制
- 时间格式转换
```

**API调用方式**:
```bash
POST /api/spider/crawl
{
    "source": "weibo",
    "keyword": "山东大学",
    "max_pages": 5,
    "dataset_name": "微博-山东大学舆情"
}
```

### ✅ 抖音爬虫

**原有路径**: `spiders/douyin.py`  
**新架构**: `backend/app/services/spider_service.py` (DouyinSpider)

保留为扩展接口，可后续完善实现。

### ✅ NLP情感分析

**原有路径**: `model/nlp.py`  
**新架构**: `backend/app/services/nlp_service.py`

```python
# 保留全部功能：
- SnowNLP情感分析
- 情感分类（positive/negative/neutral）
- 情感得分（0-1）
- jieba分词
```

**自动调用**：
- 爬虫数据保存时自动分析
- 手动添加记录时自动分析
- 批量导入时自动分析

### ✅ 词云生成

**原有路径**: `model/ciyuntu.py`  
**新架构**: `backend/app/services/wordcloud_service.py`

```python
# 保留全部功能：
- 停用词过滤
- jieba分词
- WordCloud生成
- 自定义遮罩图像
- 多种配色方案
```

**API调用**:
```bash
POST /api/wordcloud/generate
{
    "dataset_id": 1,
    "max_words": 200,
    "colormap": "viridis",
    "width": 800,
    "height": 600
}
```

### ✅ AI助手

**原有路径**: `model/ai_assistant.py`  
**新架构**: `backend/app/services/ai_service.py`

```python
# 保留并增强功能：
- SiliconFlow AI支持
- ZhipuAI GLM支持
- 流式对话
- 报告生成
- 上下文管理
```

**多Provider支持**（新增）:
```python
# 支持多种AI服务
providers = {
    'siliconflow': SiliconFlowProvider(),
    'zhipuai': ZhipuAIProvider(),
    # 可扩展：'openai', 'claude', 等
}
```

### ✅ 报告生成

**原有路径**: `utils/report_generator.py`  
**新架构**: `backend/app/api/ai.py` (generate_report)

```python
# 保留并优化功能：
- 舆情概述生成
- 详细分析
- 风险评估
- 应对建议
- 流式输出（SSE）
```

**API调用**:
```bash
POST /api/ai/report
{
    "dataset_id": 1,
    "sections": ["overview", "analysis", "risk", "strategy"],
    "provider": "zhipuai"
}
```

### ✅ 数据分析

**原有功能全部保留**:
- 情绪统计
- 趋势分析
- 地域分布
- 关键词提取
- 互动指标统计

---

## 新增功能

### 🆕 1. 多用户系统

**JWT认证**:
```javascript
// 注册
POST /api/auth/register
{
    "username": "user1",
    "email": "user1@example.com",
    "password": "password123",
    "full_name": "张三"
}

// 登录
POST /api/auth/login
{
    "username": "user1",
    "password": "password123"
}

// 返回Token
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

**用户角色**:
- ADMIN: 管理员（可管理所有用户）
- USER: 普通用户（仅访问自己的数据）

### 🆕 2. 数据隔离

**自动隔离机制**:
```python
# 所有API自动验证用户权限
dataset = db.query(DataSet).filter(
    DataSet.id == dataset_id,
    DataSet.user_id == current_user.id  # 自动过滤
).first()

# 文件系统隔离
/data/users/user_1/dataset_1/
/data/users/user_2/dataset_3/
```

### 🆕 3. 异步任务系统

**后台任务**:
```python
# 爬虫任务异步执行
background_tasks.add_task(crawl_task, dataset_id, keyword, max_pages)

# 批量数据处理异步
background_tasks.add_task(bulk_ingest_task, dataset_id, records)
```

**优势**:
- 不阻塞API响应
- 支持长时间任务
- 自动错误处理

### 🆕 4. 活动日志

**审计追踪**:
```python
# 自动记录所有操作
log_activity(
    db, user,
    action="create_dataset",
    resource="dataset",
    resource_id=dataset.id,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# 可查询历史操作
GET /api/users/me/activity-logs
```

### 🆕 5. 数据导出

**CSV导出**:
```python
# 自动导出到CSV（兼容旧版）
export_dataset_to_csv(db, dataset)

# 包含中文列名
"点赞数", "评论数", "分享数", "情感倾向"
```

### 🆕 6. 扩展性设计

**插件化爬虫**:
```python
# 注册新的爬虫
class XiaohongshuSpider(BaseSpider):
    def crawl(self, keyword, max_pages):
        # 实现
        pass

SpiderFactory.register_spider('xiaohongshu', XiaohongshuSpider)
```

**自定义AI Provider**:
```python
# 添加OpenAI支持
class OpenAIProvider(AIProvider):
    def chat_completion(self, messages, stream, **kwargs):
        # OpenAI API调用
        pass

ai_service.register_provider('openai', OpenAIProvider())
```

### 🆕 7. 实时流式响应

**SSE (Server-Sent Events)**:
```javascript
// AI报告生成实时推送
const eventSource = new EventSource('/api/ai/report');
eventSource.onmessage = (event) => {
    const chunk = JSON.parse(event.data);
    if (chunk.type === 'content') {
        appendToReport(chunk.content);
    }
};
```

### 🆕 8. 去重机制

**爬虫数据去重**:
```python
# 基于post_id自动去重
if post_id:
    exists = db.query(DataRecord).filter(
        DataRecord.dataset_id == dataset_id,
        DataRecord.post_id == post_id
    ).first()
    if exists:
        continue  # 跳过重复数据
```

---

## 架构优化

### 🏗️ 1. 模块化解耦

**Service层设计**:
```
SpiderService    - 爬虫逻辑
NLPService       - NLP分析
AIService        - AI对话/报告
AnalyticsService - 数据分析
WordCloudService - 词云生成
```

每个Service独立，互不依赖。

### 🏗️ 2. 工厂模式

**SpiderFactory**:
```python
# 统一创建爬虫实例
spider = SpiderFactory.create('weibo')

# 支持注册新类型
SpiderFactory.register_spider('new_source', NewSpider)
```

### 🏗️ 3. 策略模式

**AI Provider策略**:
```python
# 根据配置选择Provider
ai_service.get_provider('siliconflow')
ai_service.get_provider('zhipuai')
```

### 🏗️ 4. 依赖注入

**FastAPI DI系统**:
```python
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 自动注入db和user
    pass
```

---

## API端点说明

### 认证 `/api/auth`

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/register` | 注册新用户 |
| POST | `/login` | 用户登录 |
| GET | `/me` | 获取当前用户信息 |

### 数据集 `/api/datasets`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | 列出我的数据集 |
| POST | `/` | 创建数据集 |
| GET | `/{id}` | 获取数据集详情 |
| PUT | `/{id}` | 更新数据集 |
| DELETE | `/{id}` | 删除数据集 |
| POST | `/{id}/upload` | 上传文件 |
| GET | `/{id}/records` | 获取记录列表 |

### 爬虫 `/api/spider` (新增)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/crawl` | 启动爬虫任务 |
| GET | `/sources` | 列出可用数据源 |

### AI `/api/ai` (新增)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/chat` | AI对话（流式） |
| POST | `/report` | 生成AI报告（流式） |
| GET | `/providers` | 列出AI服务商 |

### 词云 `/api/wordcloud` (新增)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/generate` | 生成词云图 |

### 分析 `/api/analytics`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/{dataset_id}` | 获取分析报告 |

---

## 使用示例

### 示例1：爬取微博数据

```bash
# 1. 登录获取Token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 响应: {"access_token": "eyJ..."}

# 2. 启动爬虫
curl -X POST http://localhost:8000/api/spider/crawl \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "weibo",
    "keyword": "人工智能",
    "max_pages": 5,
    "dataset_name": "微博-AI舆情"
  }'

# 响应: {
#   "message": "Crawl task started",
#   "dataset_id": 1,
#   "estimated_records": 50
# }

# 3. 查看数据集
curl -X GET http://localhost:8000/api/datasets/1 \
  -H "Authorization: Bearer <token>"

# 4. 获取分析
curl -X GET http://localhost:8000/api/analytics/1 \
  -H "Authorization: Bearer <token>"
```

### 示例2：生成AI报告

```bash
# 流式生成报告
curl -X POST http://localhost:8000/api/ai/report \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "sections": ["overview", "analysis", "risk"],
    "provider": "zhipuai"
  }'

# 响应（SSE流）:
# data: {"type": "title", "content": "## 📊 舆情概述\n\n"}
# data: {"type": "content", "content": "本次分析..."}
# data: [DONE]
```

### 示例3：生成词云

```bash
curl -X POST http://localhost:8000/api/wordcloud/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "max_words": 100,
    "colormap": "viridis",
    "width": 800,
    "height": 600
  }'

# 响应:
# {
#   "image_base64": "iVBORw0KGgoAAAANSUhE...",
#   "word_frequencies": {
#     "人工智能": 45,
#     "技术": 32,
#     ...
#   },
#   "total_words": 1234,
#   "unique_words": 567
# }
```

### 示例4：AI对话

```bash
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "帮我分析一下这个数据集的舆情特点"}
    ],
    "stream": false
  }'

# 响应:
# {
#   "content": "根据数据分析...",
#   "usage": {"prompt_tokens": 20, "completion_tokens": 100}
# }
```

---

## 与原版的兼容性

### CSV文件格式

**保持兼容**:
```csv
post_id,content,author,publish_time,likes,shares,comments,sentiment_score,sentiment_label,点赞数,评论数,分享数,情感倾向
123,内容,作者,2024-01-01 12:00:00,100,50,30,0.8,positive,100,30,50,正面
```

### 数据结构

**数据库字段映射**:
```python
# 旧版CSV列名 → 新版数据库字段
"点赞数"     → likes
"评论数"     → comments
"分享数"     → shares
"情感倾向"   → sentiment_label
```

### API向后兼容

**保留旧版路径**（可选）:
```python
# 可添加兼容层
@router.get("/old-api/get_info2")
def legacy_get_info2(csv_path: str):
    # 调用新版API
    pass
```

---

## 扩展指南

### 添加新的爬虫

```python
# 1. 继承BaseSpider
class TwitterSpider(BaseSpider):
    def crawl(self, keyword, max_pages):
        # 实现Twitter爬虫
        results = []
        for page in range(max_pages):
            page_data = self.crawl_page(keyword, page)
            results.extend(page_data)
        return results
    
    def parse_item(self, item):
        return {
            'post_id': item['id'],
            'content': item['text'],
            'author': item['user']['name'],
            'publish_time': item['created_at'],
            'likes': item['likes_count'],
            'shares': item['retweet_count'],
            'comments': item['reply_count'],
        }

# 2. 注册
SpiderFactory.register_spider('twitter', TwitterSpider)

# 3. 使用
POST /api/spider/crawl
{
    "source": "twitter",
    "keyword": "AI",
    "max_pages": 5
}
```

### 添加新的AI Provider

```python
# 1. 实现Provider接口
class OpenAIProvider(AIProvider):
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def is_available(self):
        return self.client is not None
    
    def chat_completion(self, messages, stream, **kwargs):
        return self.client.chat.completions.create(
            model='gpt-4',
            messages=messages,
            stream=stream,
            **kwargs
        )

# 2. 注册
ai_service.register_provider('openai', OpenAIProvider())

# 3. 使用
POST /api/ai/chat
{
    "messages": [...],
    "provider": "openai"
}
```

---

## 总结

### ✅ 完全保留的功能
- 微博爬虫
- 抖音爬虫接口
- NLP情感分析
- 词云生成
- AI助手对话
- 报告生成
- 数据分析

### ✨ 新增增强功能
- 多用户系统
- 数据隔离
- JWT认证
- 异步任务
- 活动日志
- 扩展接口
- 流式响应
- 去重机制

### 🏗️ 架构优化
- 模块化解耦
- 插件化设计
- 工厂模式
- 策略模式
- 依赖注入
- RESTful API

所有原有功能都已整合到新架构中，并通过更好的设计提升了可扩展性和可维护性！
