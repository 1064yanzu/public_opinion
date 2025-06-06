# 舆情分析系统

本项目是一个使用 **Flask** 构建的舆情监测与分析平台，集成了多平台爬虫、文本情感分析、实时数据可视化以及大模型问答等功能，适用于快速搭建舆情监控与报告生成服务。

## 功能概览

- **数据采集**：内置微博、抖音等爬虫，可根据关键词定时抓取数据
- **情感分析**：利用 `SnowNLP` 对抓取的数据进行情感倾向判断
- **数据整合**：将不同平台的数据转换为统一格式，便于统计与展示
- **实时监控**：后台任务调度支持周期性爬取，前端可查看实时统计与列表
- **词云/热度分析**：生成词云图和热门话题列表，辅助了解舆情走向
- **AI 助手**：通过 `services/ai_service.py` 调用第三方大模型实现问答与报告生成
- **报表输出**：`utils/report_generator.py` 可以按需生成舆情分析报告

## 快速开始

1. **克隆仓库**
   ```bash
   git clone <repo-url>
   cd public_opinion
   ```
2. **安装依赖**（需要 Python 3.11+）
   ```bash
   pip install -r requirements.txt
   ```
3. **初始化环境**（可选，首次部署时创建目录及示例数据）
   ```bash
   python utils/init_system.py
   ```
4. **配置密钥**
   - 在 `config/settings.py` 或环境变量中设置 `ZHIPUAI_API_KEY` 等大模型相关配置
5. **启动服务**
   ```bash
   python app.py          # 开发模式
   # 或使用 gunicorn
   gunicorn -c gunicorn_conf.py app:app
   ```

访问 `http://localhost:8000` 即可进入系统首页。

## 目录结构

```
├── app.py                 # Flask 应用入口
├── config/                # 配置文件
├── services/              # 服务层，封装爬虫与 AI 调用
├── spiders/               # 各平台爬虫实现
├── model/                 # NLP 与数据处理模块
├── utils/                 # 工具函数及系统初始化脚本
├── templates/             # 前端模板
├── static/                # 静态资源
├── persistent_data/       # 持久化爬取结果
└── temp_data/             # 临时文件和中间结果
```

## 开发与扩展

- **新增爬虫**：在 `spiders/` 目录中编写爬虫脚本，并在 `services/crawler_service.py` 中调用
- **替换大模型**：调整 `services/ai_service.py` 中的实现或在 `model/ai_assistant.py` 配置不同的 API
- **定制报告**：修改 `utils/report_generator.py` 中的生成逻辑，可自定义章节和模板

## 许可证

本项目采用 MIT License 发布，详情见 LICENSE 文件。
