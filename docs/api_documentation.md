# 舆情分析系统 API 接口文档

> **版本**: 2.0.0  
> **基础路径**: `/api`  
> **认证方式**: JWT Bearer Token

---

## 目录

1. [认证接口](#认证接口)
2. [爬虫接口](#爬虫接口)
3. [数据分析接口](#数据分析接口)
4. [页面数据接口](#页面数据接口)
5. [AI助手接口](#ai助手接口)
6. [高级分析接口](#高级分析接口)
7. [系统监控接口](#系统监控接口)
8. [系统配置接口](#系统配置接口)
9. [数据模型](#数据模型)
10. [错误码说明](#错误码说明)

---

## 认证接口

### 用户注册

```
POST /api/auth/register
```

**描述**: 创建新用户账号

**请求体**:
```json
{
  "username": "string",  // 用户名，3-50字符
  "email": "user@example.com",  // 邮箱地址
  "password": "string"  // 密码，至少6字符
}
```

**响应** (201):
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-26T10:00:00Z"
}
```

**错误**:
- `400`: 用户名或邮箱已存在

---

### 用户登录

```
POST /api/auth/login
```

**描述**: 用户登录并获取访问令牌

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-12-26T10:00:00Z"
  }
}
```

**错误**:
- `401`: 用户名或密码错误
- `400`: 用户已被禁用

---

### 获取当前用户

```
GET /api/auth/me
```

**描述**: 获取当前登录用户信息

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-26T10:00:00Z"
}
```

---

### 更新用户信息

```
PUT /api/auth/me
```

**描述**: 更新当前用户信息

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "email": "newemail@example.com"  // 可选
}
```

**响应** (200): 返回更新后的用户信息

---

### 用户登出

```
POST /api/auth/logout
```

**描述**: 用户登出（客户端需删除令牌）

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "message": "登出成功",
  "success": true
}
```

---

## 爬虫接口

### 创建搜索任务

```
POST /api/spider/search
```

**描述**: 创建微博或抖音搜索爬虫任务

**请求头** (可选):
```
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "task_type": "weibo",  // "weibo" 或 "douyin"
  "keyword": "北京冬奥会",  // 搜索关键词
  "max_page": 10,  // 最大爬取页数，1-50
  "async_mode": false,  // 是否异步执行
  "config": {}  // 额外配置（可选）
}
```

**响应** (200):
```json
{
  "id": 1,
  "user_id": 1,
  "task_type": "weibo",
  "keyword": "北京冬奥会",
  "max_page": 10,
  "status": "processing",
  "progress": 0,
  "error_message": null,
  "created_at": "2025-12-26T10:00:00Z",
  "started_at": "2025-12-26T10:00:01Z",
  "completed_at": null
}
```

---

### 获取任务列表

```
GET /api/spider/tasks
```

**描述**: 获取爬虫任务列表

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 (1-100) |
| status | string | - | 任务状态筛选 |

**响应** (200):
```json
{
  "total": 10,
  "tasks": [
    {
      "id": 1,
      "task_type": "weibo",
      "keyword": "北京冬奥会",
      "status": "completed",
      "progress": 100,
      "created_at": "2025-12-26T10:00:00Z",
      "completed_at": "2025-12-26T10:05:00Z"
    }
  ]
}
```

---

### 获取任务详情

```
GET /api/spider/tasks/{task_id}
```

**描述**: 获取指定任务的详细信息

**路径参数**:
- `task_id`: 任务ID

**响应** (200): 返回任务详情

**错误**:
- `404`: 任务不存在

---

### 取消任务

```
POST /api/spider/tasks/{task_id}/cancel
```

**描述**: 取消正在执行的任务

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "message": "任务已取消",
  "success": true
}
```

---

### 获取微博数据

```
GET /api/spider/weibo
```

**描述**: 获取微博爬虫数据列表

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |
| task_id | int | - | 任务ID筛选 |
| keyword | string | - | 内容关键词搜索 |
| sentiment | string | - | 情感筛选 (positive/negative/neutral) |

**响应** (200):
```json
{
  "total": 100,
  "data": [
    {
      "id": 1,
      "weibo_id": "4123456789",
      "content": "微博内容...",
      "user_name": "用户昵称",
      "publish_time": "2025-12-26T10:00:00Z",
      "like_count": 100,
      "comment_count": 50,
      "share_count": 20,
      "sentiment_score": 0.85,
      "sentiment_label": "positive"
    }
  ]
}
```

---

### 获取抖音数据

```
GET /api/spider/douyin
```

**描述**: 获取抖音爬虫数据列表

**查询参数**: 同微博数据接口

**响应** (200): 结构类似微博数据

---

## 数据分析接口

### 获取主页数据

```
GET /api/analysis/home
```

**描述**: 获取主页展示所需的统计数据

**响应** (200):
```json
{
  "stats": {
    "total_count": 1000,
    "today_count": 50,
    "positive_count": 600,
    "negative_count": 200,
    "neutral_count": 200
  },
  "sentiment_distribution": {
    "positive": 60.0,
    "negative": 20.0,
    "neutral": 20.0
  },
  "recent_data": [...],
  "hotspots": [...]
}
```

---

### 获取统计数据

```
GET /api/analysis/stats
```

**描述**: 获取数据统计信息

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| task_id | int | 任务ID筛选 |

**响应** (200):
```json
{
  "total_count": 1000,
  "today_count": 50,
  "positive_count": 600,
  "negative_count": 200,
  "neutral_count": 200
}
```

---

### 情感分析

```
POST /api/analysis/sentiment
```

**描述**: 对给定文本进行情感分析

**请求体**:
```json
{
  "texts": [
    "这个产品真的很好用！",
    "服务态度太差了，非常失望。"
  ]
}
```

**响应** (200):
```json
{
  "results": [
    {
      "text": "这个产品真的很好用！",
      "sentiment": "positive",
      "score": 0.92
    },
    {
      "text": "服务态度太差了，非常失望。",
      "sentiment": "negative",
      "score": 0.15
    }
  ]
}
```

---

### 生成词云

```
POST /api/analysis/wordcloud
```

**描述**: 根据关键词生成词云

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| keyword | string | 关键词（必填） |
| task_id | int | 任务ID（可选） |

**响应** (200):
```json
{
  "image_url": "/static/wordcloud/xxx.png",
  "word_freq": {
    "冬奥会": 125,
    "北京": 98,
    "运动员": 67
  }
}
```

---

### 生成报告

```
POST /api/analysis/report
```

**描述**: 根据关键词生成分析报告

**请求体**:
```json
{
  "keyword": "北京冬奥会",
  "report_type": "comprehensive"  // comprehensive/sentiment/trend
}
```

**响应** (200):
```json
{
  "report_id": "report_20251226_abc123",
  "status": "completed",
  "download_url": "/api/analysis/report/download/report_20251226_abc123",
  "content": {
    "title": "北京冬奥会舆情分析报告",
    "summary": "共分析 1000 条相关数据",
    "sentiment_distribution": {
      "positive": 60.0,
      "neutral": 25.0,
      "negative": 15.0
    }
  }
}
```

---

## 页面数据接口

### 获取主页数据（异步加载）

```
GET /api/page/home-data
```

**描述**: 异步加载主页展示数据，包括统计信息、最近数据和热点新闻

**响应** (200):
```json
{
  "success": true,
  "data": {
    "unique_user_count": 1000,
    "total_heat_value": 50000,
    "unique_ip_count": 600,
    "row_count": 1000,
    "infos2_data": [
      {
        "author": "用户名",
        "content": "微博内容...",
        "time": "2025-12-26 10:00",
        "shares": 20,
        "comments": 50,
        "likes": 100,
        "url": "https://...",
        "sentiment": "positive"
      }
    ],
    "daily_hotspots": [
      {
        "title": "热点标题",
        "source": "来源",
        "link": "https://...",
        "cover_image": "https://..."
      }
    ]
  }
}
```

---

### 获取图表数据

```
GET /api/page/chart-data
```

**描述**: 获取情感分布、地域分布等图表数据

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| task_id | int | 任务ID筛选（可选） |

**响应** (200):
```json
{
  "heatmap_data": [
    {"name": "北京", "value": 150},
    {"name": "上海", "value": 120}
  ],
  "sentiment_data": {
    "正面": 600,
    "负面": 200,
    "中性": 200
  },
  "gender_data": {
    "男": 500,
    "女": 500
  }
}
```

---

### 获取热点话题

```
GET /api/page/hot-topics
```

**描述**: 获取当前热点话题列表

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| limit | int | 50 | 返回数量 (1-100) |

**响应** (200): 返回热点话题数组

---

### 获取实时监控数据

```
GET /api/page/realtime-monitoring
```

**描述**: 获取实时舆情监控数据

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| limit | int | 100 | 返回数量 (1-500) |

**响应** (200):
```json
[
  {
    "author": "用户名",
    "content": "内容...",
    "Link": "https://...",
    "authorUrl": "https://..."
  }
]
```

---

### 获取实时数据

```
GET /api/page/realtime-data
```

**描述**: 获取实时舆情分析数据

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| keyword | string | 关键词筛选（可选） |
| limit | int | 返回数量 (1-200) |

**响应** (200):
```json
{
  "total": 50,
  "sentiment_distribution": {
    "positive": 60.0,
    "negative": 20.0,
    "neutral": 20.0
  },
  "data": [...]
}
```

---

### 获取任务状态

```
GET /api/page/status
```

**描述**: 获取当前系统任务状态

**响应** (200):
```json
{
  "status": "idle",
  "message": "系统空闲，可接受新任务"
}
```
或
```json
{
  "status": "working",
  "message": "正在执行任务：北京冬奥会",
  "task_id": 1,
  "progress": 50
}
```

---

### 生成词云

```
POST /api/page/wordcloud
```

**描述**: 根据数据生成词云图片

**请求体**:
```json
{
  "keyword": "北京冬奥会",
  "task_id": 1
}
```

**响应** (200):
```json
{
  "image_url": "/static/wordcloud/wordcloud_20251226.png",
  "word_freq": {
    "冬奥会": 125,
    "北京": 98
  },
  "message": "词云生成成功"
}
```

---

### 获取案例列表

```
GET /api/page/cases
```

**描述**: 获取舆情案例列表

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 10 | 每页数量 |

**响应** (200):
```json
{
  "total": 50,
  "cases": [
    {
      "id": 1,
      "keyword": "北京冬奥会",
      "type": "weibo",
      "created_at": "2025-12-26T10:00:00",
      "completed_at": "2025-12-26T10:05:00"
    }
  ]
}
```

---

### 获取案例详情

```
GET /api/page/cases/{case_id}
```

**描述**: 基于已完成任务返回某个案例的真实详情，用于 React 案例库页面展示。

**响应** (200):
```json
{
  "id": 8,
  "keyword": "某热点事件",
  "task_type": "weibo",
  "status": "completed",
  "created_at": "2026-04-15T12:00:00",
  "completed_at": "2026-04-15T12:08:00",
  "statistics": {
    "total_count": 120,
    "total_likes": 3400,
    "total_comments": 560,
    "total_shares": 180,
    "total_interaction": 4140,
    "sentiment_distribution": {
      "positive": 30,
      "neutral": 60,
      "negative": 30
    }
  },
  "risk": {
    "level": "中",
    "score": 42.5,
    "factors": [
      "负面情感占比较高 (25.0%)"
    ]
  },
  "topics": [],
  "spreaders": [],
  "recent_items": []
}
```

**错误**:
- `404`: 案例不存在

---

### 获取舆情应对手册正文

```
GET /api/page/manual-content
```

**描述**: 读取项目根目录中的真实 `网络舆情应对手册.md` 文件，供 React 手册页面直接渲染。

**响应** (200):
```json
{
  "title": "网络舆情应对手册",
  "markdown": "# 手册正文 ...",
  "source_path": "/abs/path/网络舆情应对手册.md",
  "updated_at": "1744712770"
}
```

---

## AI助手接口

### AI 聊天

```
POST /api/ai/chat
```

**描述**: 与 AI 助手进行对话

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "message": "请分析一下最近的舆情趋势",
  "history": [
    {"role": "user", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
  ],
  "stream": false
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "根据最近的数据分析...",
  "error": null
}
```

---

### AI 流式聊天

```
POST /api/ai/chat-stream
```

**描述**: 与 AI 助手进行流式对话（Server-Sent Events）

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求体**: 同 AI 聊天接口

**响应**: SSE 格式流式输出
```
data: {"content": "根据"}
data: {"content": "最近"}
data: {"content": "的数据..."}
data: {"done": true}
```

---

### 获取聊天历史

```
GET /api/ai/chat-history
```

**描述**: 获取当前用户的聊天历史记录

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| limit | int | 50 | 返回数量 (1-200) |

**响应** (200):
```json
{
  "history": [
    {"role": "user", "content": "问题"},
    {"role": "assistant", "content": "回答"}
  ],
  "total": 10
}
```

---

### 清空聊天历史

```
POST /api/ai/clear-chat
```

**描述**: 清空当前用户的聊天历史记录

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "success": true,
  "message": "聊天历史已清空"
}
```

---

### 分析文本

```
POST /api/ai/analyze-text
```

**描述**: 使用 AI 分析文本的情感倾向和关键信息

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| text | string | 待分析的文本（必填） |

**响应** (200):
```json
{
  "success": true,
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "keywords": ["关键词1", "关键词2"],
  "summary": ["摘要句子"],
  "method": "snownlp"
}
```

---

## 高级分析接口

### 关键传播主体识别

```
GET /api/advanced/key-spreaders
```

**描述**: 识别数据中最具影响力的传播主体

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| task_id | int | - | 任务ID筛选 |
| keyword | string | - | 关键词筛选 |
| top_n | int | 20 | 返回数量 (1-100) |
| platform | string | weibo | 平台 (weibo/douyin) |

**响应** (200):
```json
{
  "spreaders": [
    {
      "user_name": "用户名",
      "user_id": "123456",
      "post_count": 15,
      "total_likes": 5000,
      "total_comments": 1200,
      "total_shares": 800,
      "followers": 50000,
      "avg_interaction": 466.67,
      "influence_score": 12500.5
    }
  ],
  "total": 20,
  "data_count": 500
}
```

---

### 主题聚类分析

```
GET /api/advanced/topics
```

**描述**: 对文本进行主题聚类，识别主要话题

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| task_id | int | - | 任务ID筛选 |
| keyword | string | - | 关键词筛选 |
| n_topics | int | 5 | 主题数量 (2-10) |
| words_per_topic | int | 10 | 每个主题的关键词数 (5-20) |

**响应** (200):
```json
{
  "topics": [
    {
      "topic_id": 1,
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "keyword_weights": [
        {"word": "关键词1", "weight": 0.15},
        {"word": "关键词2", "weight": 0.12}
      ],
      "doc_count": 120,
      "doc_ratio": 0.24
    }
  ],
  "total_docs": 500
}
```

---

### 趋势分析

```
GET /api/advanced/trend
```

**描述**: 分析数据随时间的变化趋势

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| task_id | int | - | 任务ID筛选 |
| keyword | string | - | 关键词筛选 |
| interval | string | day | 时间间隔 (hour/day/week) |

**响应** (200):
```json
{
  "timeline": [
    {
      "time": "2025-12-26",
      "count": 50,
      "likes": 1200,
      "comments": 300,
      "shares": 150,
      "positive": 30,
      "negative": 10,
      "sentiment_ratio": 0.6
    }
  ],
  "stats": {
    "total": 500,
    "time_range": {
      "start": "2025-12-20",
      "end": "2025-12-26"
    },
    "peak_time": "2025-12-24",
    "avg_per_period": 71.43
  }
}
```

---

### 情感演化分析

```
GET /api/advanced/sentiment-evolution
```

**描述**: 分析情感随时间的变化趋势

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| task_id | int | 任务ID筛选 |
| keyword | string | 关键词筛选 |

**响应** (200):
```json
{
  "evolution": [
    {
      "time": "2025-12-26",
      "positive_ratio": 0.6,
      "negative_ratio": 0.2,
      "neutral_ratio": 0.2,
      "total": 50
    }
  ],
  "trend_direction": "improving"
}
```

---

### 正负面关键词对比

```
GET /api/advanced/keyword-comparison
```

**描述**: 对比正面和负面文本的关键词差异

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| task_id | int | - | 任务ID筛选 |
| keyword | string | - | 关键词筛选 |
| top_n | int | 15 | 每类返回数量 (5-30) |

**响应** (200):
```json
{
  "positive": [
    {"word": "好评", "count": 50},
    {"word": "优秀", "count": 35}
  ],
  "negative": [
    {"word": "差评", "count": 30},
    {"word": "失望", "count": 25}
  ],
  "common": [
    {"word": "产品", "count": 100}
  ],
  "positive_count": 200,
  "negative_count": 100
}
```

---

### 生成词云（高级）

```
POST /api/advanced/wordcloud
```

**描述**: 根据数据生成词云图片和词频统计

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| task_id | int | - | 任务ID筛选 |
| keyword | string | - | 关键词筛选 |
| max_words | int | 200 | 最大词数 (50-500) |

**响应** (200):
```json
{
  "image_url": "/static/wordcloud/wordcloud_20251226_120000.png",
  "word_freq": {
    "关键词1": 150,
    "关键词2": 120,
    "关键词3": 95
  },
  "total_words": 200,
  "message": "词云生成成功"
}
```

---

## 系统监控接口

---

## 系统配置接口

### 获取系统配置

```
GET /api/system/config
```

**描述**: 获取当前保存的桌面系统配置，以及后端当前生效的运行时快照。

**响应** (200):
```json
{
  "config": {
    "app_name": "舆情分析系统",
    "ai_model_type": "zhipuai",
    "ai_api_key": "",
    "ai_base_url": "",
    "ai_model_id": "",
    "weibo_cookie": "",
    "douyin_cookie": "",
    "crawler_max_page": 10,
    "crawler_timeout": 30,
    "crawler_delay": 1,
    "data_dir": "/Users/chen/Library/Application Support/public_opinion/data",
    "reports_dir": "/Users/chen/Library/Application Support/public_opinion/reports",
    "wordcloud_dir": "/Users/chen/Library/Application Support/public_opinion/static/wordcloud",
    "database_path": "/Users/chen/Library/Application Support/public_opinion/database/public_opinion.db",
    "log_dir": "/Users/chen/Library/Application Support/public_opinion/logs"
  },
  "active_runtime": {
    "APP_NAME": "舆情分析系统",
    "API_HOST": "127.0.0.1",
    "API_PORT": 8000,
    "DESKTOP_MODE": true
  },
  "config_path": "/.../runtime-config.json",
  "restart_required": false
}
```

### 更新系统配置

```
PUT /api/system/config
```

**描述**: 更新桌面系统配置文件。

**请求体**:
```json
{
  "ai_model_type": "openai",
  "ai_api_key": "sk-***",
  "ai_base_url": "https://api.openai.com/v1",
  "weibo_cookie": "SUB=...; SUBP=...",
  "reports_dir": "/Users/chen/Documents/PublicOpinion/reports"
}
```

**响应** (200):
```json
{
  "config": {
    "ai_model_type": "openai",
    "ai_api_key": "sk-***",
    "ai_base_url": "https://api.openai.com/v1",
    "reports_dir": "/Users/chen/Documents/PublicOpinion/reports"
  },
  "active_runtime": {},
  "config_path": "/.../runtime-config.json",
  "restart_required": true
}
```

### 获取桌面运行时状态

```
GET /api/system/runtime
```

**描述**: 获取当前后端运行环境、路径和桌面模式状态。

**响应** (200):
```json
{
  "desktop_mode": true,
  "api_host": "127.0.0.1",
  "api_port": 18743,
  "app_data_dir": "/Users/chen/Library/Application Support/public_opinion",
  "static_dir": "/Users/chen/Library/Application Support/public_opinion/static",
  "reports_dir": "/Users/chen/Library/Application Support/public_opinion/reports",
  "wordcloud_dir": "/Users/chen/Library/Application Support/public_opinion/static/wordcloud",
  "database_path": "/Users/chen/Library/Application Support/public_opinion/database/public_opinion.db",
  "config_path": "/Users/chen/Library/Application Support/public_opinion/config/runtime-config.json"
}
```

### 健康检查

```
GET /api/monitor/health
```

**描述**: 检查系统健康状态（无需认证）

**响应** (200):
```json
{
  "status": "healthy",
  "service": "舆情分析系统",
  "version": "2.0.0",
  "timestamp": "2025-12-26T10:00:00Z",
  "uptime": 86400
}
```

---

### 性能统计

```
GET /api/monitor/performance
```

**描述**: 获取系统性能统计信息

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 62.8,
  "disk_usage": 38.5,
  "uptime": 86400
}
```

---

### 缓存统计

```
GET /api/monitor/cache
```

**描述**: 获取缓存统计信息

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "total_size": 1048576,
  "item_count": 245,
  "hit_rate": 0.85
}
```

---

### 清空缓存

```
POST /api/monitor/cache/clear
```

**描述**: 清空系统缓存

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "message": "缓存已清空，共清除 245 项",
  "success": true
}
```

---

### 获取告警

```
GET /api/monitor/alerts
```

**描述**: 获取系统告警信息

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| limit | int | 50 | 返回数量限制 (1-100) |

**响应** (200):
```json
{
  "alerts": [
    {
      "id": "cpu_1703577600",
      "level": "warning",
      "type": "cpu_high",
      "message": "CPU 使用率过高: 85.2%",
      "timestamp": "2025-12-26T10:00:00Z",
      "resolved": false
    }
  ],
  "total": 5,
  "unresolved": 2
}
```

---

### 检查告警

```
POST /api/monitor/alerts/check
```

**描述**: 手动触发告警检查

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "message": "系统正常，无告警",
  "success": true
}
```

---

### 系统信息

```
GET /api/monitor/system
```

**描述**: 获取系统详细信息

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应** (200):
```json
{
  "system": "Darwin",
  "platform": "macOS-14.0-arm64",
  "python_version": "3.10.0",
  "cpu_count": 8,
  "memory_total": 17179869184,
  "memory_available": 8589934592,
  "disk_total": 500000000000,
  "disk_free": 200000000000,
  "uptime": 86400,
  "start_time": "2025-12-25T10:00:00"
}
```

---

## 数据模型

### 任务状态 (TaskStatus)

| 值 | 描述 |
|----|------|
| pending | 等待中 |
| processing | 处理中 |
| completed | 已完成 |
| failed | 失败 |
| cancelled | 已取消 |

### 任务类型 (TaskType)

| 值 | 描述 |
|----|------|
| weibo | 微博 |
| douyin | 抖音 |

### 情感标签 (SentimentLabel)

| 值 | 描述 |
|----|------|
| positive | 正面 |
| negative | 负面 |
| neutral | 中性 |

---

## 错误码说明

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "错误详细信息"
}
```

---

## 认证说明

### 获取 Token

1. 调用 `POST /api/auth/login` 登录
2. 从响应中获取 `access_token`
3. 在后续请求头中添加：`Authorization: Bearer {access_token}`

### Token 有效期

- 默认有效期：7 天（604800 秒）
- 过期后需重新登录

---

## 快速开始示例

### JavaScript/TypeScript

```typescript
// 登录
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: '123456' })
});
const { access_token } = await loginResponse.json();

// 创建爬虫任务
const taskResponse = await fetch('/api/spider/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    task_type: 'weibo',
    keyword: '北京冬奥会',
    max_page: 10
  })
});
const task = await taskResponse.json();
```

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# 登录
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "123456"
})
token = response.json()["access_token"]

# 创建爬虫任务
response = requests.post(
    f"{BASE_URL}/spider/search",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "task_type": "weibo",
        "keyword": "北京冬奥会",
        "max_page": 10
    }
)
task = response.json()
```

---

## API 文档访问

启动后端服务后，可访问交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 版本历史

### v2.0.0 (2025-12-26)

- 🎉 完全重构为 FastAPI
- ✨ 前后端分离架构
- ✨ JWT 认证
- ✨ SQLite 数据库
- ✨ 异步任务支持
- 📝 完整 API 文档
