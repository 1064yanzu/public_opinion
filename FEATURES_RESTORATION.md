# 🔧 核心功能恢复计划

> **状态**: 进行中  
> **目标**: 在现代化架构下恢复所有原有核心功能

---

## ✅ 已完成的基础功能

1. **用户认证系统** - JWT Token认证
2. **数据集管理** - CRUD操作
3. **数据记录管理** - 单条/批量导入
4. **情感分析** - SnowNLP集成
5. **基础数据可视化** - ECharts图表

---

## 🚧 需要恢复的核心功能

### 1. 爬虫系统 (Spider System)

#### 1.1 已添加的API端点
- ✅ `POST /api/spider/task` - 创建爬虫任务
- ✅ `GET /api/spider/history` - 获取历史记录
- ✅ `GET /api/spider/status/{task_id}` - 获取任务状态
- ✅ `POST /api/spider/stop/{task_id}` - 停止任务
- ✅ `GET /api/spider/hot-topics` - 获取热点话题
- ✅ `GET /api/spider/realtime-data` - 获取实时数据
- ✅ `GET /api/spider/chart-data` - 获取图表数据

#### 1.2 需要实现的功能
- ⏳ Spider Service完整实现（复用现有spiders目录）
- ⏳ 任务调度器集成（APScheduler）
- ⏳ 多平台爬虫支持：
  - 微博爬虫
  - 抖音爬虫
  - B站爬虫
  - 澎湃新闻

#### 1.3 前端页面
- ⏳ SpiderSettingsPage - 爬虫配置页面
- ⏳ SpiderMonitorPage - 实时监控页面
- ⏳ HotTopicsCard - 热点话题卡片

---

### 2. 舆情报告生成 (Report Generation)

#### 2.1 已添加的API端点
- ✅ `POST /api/report/generate` - 生成报告（流式）
- ✅ `GET /api/report/history` - 报告历史
- ✅ `POST /api/report/export/{report_id}` - 导出报告

#### 2.2 需要实现的功能
- ⏳ Report Service完整实现
- ⏳ 流式报告生成
- ⏳ 多深度级别支持（简单/标准/详细）
- ⏳ 报告结构化输出：
  - 舆情概述
  - 数据分析
  - 情感趋势
  - 地域分布
  - 应对建议
  - 风险提示

#### 2.3 前端页面
- ⏳ ReportGeneratorPage - 报告生成页面
- ⏳ ReportViewerPage - 报告查看页面
- ⏳ ReportHistoryPage - 历史报告列表

---

### 3. 案例库系统 (Case Library)

#### 3.1 已添加的API端点
- ✅ `GET /api/cases/` - 获取案例列表
- ✅ `GET /api/cases/{id}` - 获取案例详情
- ✅ `POST /api/cases/` - 创建案例（管理员）
- ✅ `PUT /api/cases/{id}` - 更新案例（管理员）
- ✅ `DELETE /api/cases/{id}` - 删除案例（管理员）
- ✅ `GET /api/cases/categories/list` - 获取分类列表
- ✅ `GET /api/cases/search/similar` - 搜索相似案例

#### 3.2 案例分类
- 政治类
- 经济类
- 社会类
- 文化类
- 突发事件类
- 企业公关类

#### 3.3 前端页面
- ⏳ CaseLibraryPage - 案例库主页
- ⏳ CaseDetailPage - 案例详情页
- ⏳ CaseManagePage - 案例管理（管理员）
- ⏳ CaseSearchPage - 案例搜索

---

### 4. AI助手系统 (AI Assistant)

#### 4.1 需要添加的API端点
- ⏳ `POST /api/ai/chat` - AI对话
- ⏳ `POST /api/ai/chat-stream` - 流式对话
- ⏳ `GET /api/ai/history` - 对话历史
- ⏳ `POST /api/ai/clear` - 清除历史
- ⏳ `POST /api/ai/verify-password` - 验证访问密码

#### 4.2 AI功能
- 智能问答
- 策略建议
- 风险评估
- 报告解读
- 案例推荐

#### 4.3 前端页面
- ⏳ AIAssistantPage - AI助手页面
- ⏳ ChatInterface - 对话界面组件

---

### 5. 词云生成 (Word Cloud)

#### 5.1 已有的API端点
- ✅ `GET /api/wordcloud/{dataset_id}` - 生成词云
- ✅ `POST /api/wordcloud/generate` - 异步生成

#### 5.2 需要优化的功能
- ⏳ 关键词提取优化（jieba分词）
- ⏳ 停用词过滤
- ⏳ 词频统计
- ⏳ 多种词云样式

#### 5.3 前端组件
- ⏳ WordCloudView - 词云展示组件
- ⏳ KeywordsTable - 关键词列表

---

### 6. 应对策略系统 (Response Strategy)

#### 6.1 需要添加的功能
- ⏳ 基于案例库的策略推荐
- ⏳ 基于AI的智能建议
- ⏳ 风险等级评估
- ⏳ 应急预案生成

#### 6.2 前端页面
- ⏳ StrategyPage - 应对策略页面
- ⏳ RiskAssessmentPage - 风险评估页面

---

### 7. 数据可视化增强

#### 7.1 需要添加的图表
- ⏳ 地域热力图（省份分布）
- ⏳ 时间趋势图（24小时/7天/30天）
- ⏳ 情感分布饼图
- ⏳ 性别分布统计
- ⏳ 传播路径图
- ⏳ 影响力排行

#### 7.2 实时监控
- ⏳ 实时数据流
- ⏳ 预警提示
- ⏳ 热度指数
- ⏳ 风险等级

---

## 📝 实现步骤

### 第一阶段：核心业务逻辑（1-2天）
1. ✅ 完善Spider Service
   - 集成现有爬虫代码
   - 实现任务调度
   - 数据存储和管理

2. ✅ 完善Report Service
   - 集成report_generator.py
   - 实现流式生成
   - 报告模板优化

3. ✅ 实现AI Service
   - 对话管理
   - 历史记录
   - 智能推荐

### 第二阶段：前端页面开发（2-3天）
1. 爬虫管理页面
2. 报告生成页面
3. 案例库页面
4. AI助手页面
5. 数据可视化增强

### 第三阶段：功能整合和测试（1-2天）
1. 前后端联调
2. 功能测试
3. 性能优化
4. 文档完善

---

## 🔗 依赖关系

### 现有代码复用
- ✅ `/spiders/` - 爬虫模块（微博、抖音、B站）
- ✅ `/utils/report_generator.py` - 报告生成器
- ✅ `/model/nlp.py` - NLP分析
- ✅ `/model/ciyuntu.py` - 词云生成
- ✅ `/model/ai_assistant.py` - AI助手

### 需要迁移的工具
- ✅ `utils/tools.py` - 爬虫调度工具
- ✅ `utils/common.py` - 通用工具函数
- ✅ `config/settings.py` - 配置管理

---

## 🎯 优先级

### 高优先级（必须恢复）
1. **爬虫系统** - 核心数据采集功能
2. **报告生成** - 核心输出功能
3. **数据可视化** - 数据展示

### 中优先级（重要功能）
4. **案例库** - 参考和学习
5. **AI助手** - 智能辅助
6. **词云生成** - 文本分析

### 低优先级（增强功能）
7. **应对策略** - 智能推荐
8. **实时监控** - 高级功能

---

## 📊 功能对比

| 功能模块 | v1.0 (Flask) | v2.0 (FastAPI+React) | 状态 |
|---------|-------------|---------------------|------|
| 用户认证 | ✅ Session | ✅ JWT Token | ✅ 完成 |
| 数据集管理 | ✅ | ✅ | ✅ 完成 |
| 情感分析 | ✅ | ✅ | ✅ 完成 |
| 基础可视化 | ✅ | ✅ | ✅ 完成 |
| 爬虫系统 | ✅ | ⏳ API完成 | 🚧 进行中 |
| 报告生成 | ✅ | ⏳ API完成 | 🚧 进行中 |
| 案例库 | ✅ | ✅ | ✅ 完成 |
| AI助手 | ✅ | ⏳ 待实现 | ⏳ 计划中 |
| 词云生成 | ✅ | ✅ | ✅ 完成 |
| 实时监控 | ✅ | ⏳ 待实现 | ⏳ 计划中 |

---

## 💡 技术方案

### 爬虫系统
```python
# 复用现有爬虫，封装为Service
class SpiderService:
    def execute_spider_task(self, keyword, platforms, ...):
        # 调用 spiders/ 目录下的爬虫
        from spiders.weibo import WeiboSpider
        from spiders.douyin import DouyinSpider
        # ...
```

### 报告生成
```python
# 复用现有报告生成器
class ReportService:
    def __init__(self):
        self.generator = ReportGenerator(csv_path)
    
    async def generate_report_stream(self, ...):
        # 流式生成报告
        for chunk in self.generator.generate_stream(...):
            yield chunk
```

### AI助手
```python
# 集成现有AI模块
class AIService:
    def chat(self, message, history):
        from model.ai_assistant import get_chat_response
        return get_chat_response(message, history)
```

---

## 🎨 UI设计方案

### 页面列表
1. **SpiderPage** - 爬虫配置和监控
2. **ReportPage** - 报告生成和查看
3. **CasePage** - 案例库浏览
4. **AIPage** - AI助手对话
5. **MonitorPage** - 实时监控大屏

### 组件设计
- SpiderTaskForm - 爬虫任务表单
- ReportViewer - 报告查看器
- CaseCard - 案例卡片
- ChatBox - 对话框
- HeatMap - 热力图
- TrendChart - 趋势图

---

## 🔍 下一步行动

1. **立即实施**：
   - 完善SpiderService实现
   - 完善ReportService实现
   - 添加AI相关API

2. **短期目标**：
   - 创建所有前端页面
   - 实现核心交互功能
   - 完成数据流闭环

3. **长期优化**：
   - 性能优化
   - 用户体验提升
   - 功能扩展

---

**更新时间**: 2024-10-17  
**负责人**: Development Team  
**预计完成**: 1-2周
