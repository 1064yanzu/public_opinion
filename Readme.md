# 舆情监测系统

## 项目概述

这是一个基于Flask的舆情监测系统，旨在爬取、分析和展示社交媒体数据，为用户提供实时的舆情分析和可视化服务。本系统主要关注微博平台的数据，通过高效的爬虫技术和先进的自然语言处理算法，为用户提供深入的舆情洞察。

## 主要功能

1. 数据爬取：自动从微博等社交媒体平台爬取指定关键词的相关数据
2. 数据分析：对爬取的数据进行情感分析、热点话题提取、用户画像分析等
3. 可视化展示：通过图表、地图等方式直观展示分析结果
4. 用户管理：支持用户注册、登录、密码重置等功能
5. 实时监控：对特定话题进行实时监控，及时发现舆情变化
6. 报告生成：自动生成舆情分析报告

## 技术栈

- 后端：Flask, SQLAlchemy, Celery
- 前端：HTML, CSS, JavaScript, ECharts
- 数据库：MySQL
- 爬虫：Requests, BeautifulSoup
- 数据分析：Pandas, NumPy, NLTK
- 其他：Redis (用于缓存和任务队列)

## 项目结构

```
flaskProject/
│
├── spiders/                # 爬虫脚本
│   ├── articles_spider.py  # 微博爬虫
│   ├── douyin.py           # 抖音爬虫
│   └── ...
│
├── static/                 # 静态文件
│   ├── assets/             # CSS, JS, 图片等资源
│   ├── content/            # 内容相关的静态文件
│   └── ...
│
├── views/                  # 视图函数
│   ├── page/               # 页面相关视图
│   │   ├── templates/      # 页面模板
│   │   └── page.py         # 页面路由和逻辑
│   │
│   └── user/               # 用户相关视图
│       ├── templates/      # 用户相关模板
│       └── user.py         # 用户路由和逻辑
│
├── model/                  # 数据模型和数据库操作
│   ├── __init__.py
│   └── nlp.py              # NLP相关模型和函数
│
├── utils/                  # 工具函数
│   ├── __init__.py
│   └── helpers.py          # 辅助函数
│
├── config.py               # 配置文件
├── app.py                  # Flask应用主文件
├── requirements.txt        # 项目依赖
└── README.md               # 项目说明文档
```

## 安装和配置

1. 克隆仓库：
   ```
   git clone https://github.com/yourusername/sentiment-analysis-system.git
   cd sentiment-analysis-system
   ```

2. 创建并激活虚拟环境：
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

4. 配置数据库：
   - 在MySQL中创建一个新的数据库
   - 复制 `config.py.example` 为 `config.py` 并填写正确的数据库连接信息

5. 初始化数据库：
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. 配置环境变量：
   ```
   export FLASK_APP=app.py
   export FLASK_ENV=development
   ```

## 运行应用

1. 启动Flask应用：
   ```
   flask run
   ```

2. 在浏览器中访问 `http://localhost:5000`

## 使用指南

1. 注册和登录：
   - 访问首页，点击"注册"按钮
   - 填写用户名、邮箱和密码，完成注册
   - 使用注册的账号登录系统

2. 设置爬虫：
   - 登录后，导航到"爬虫设置"页面
   - 选择目标平台（如微博、抖音等）
   - 输入关键词、时间范围、数据量等参数
   - 点击"保存设置"按钮

3. 启动爬虫：
   - 在爬虫设置页面，检查设置是否正确
   - 点击"开始爬取"按钮
   - 系统会在后台开始数据收集，可以在"任务管理"页面查看进度

4. 查看分析结果：
   - 导航到"数据分析"页面
   - 选择要分析的数据集（基于爬取的时间或关键词）
   - 系统会自动生成各种分析图表，包括：
     - 情感分析饼图
     - 热门话题词云
     - 用户活跃度柱状图
     - 地理分布热力图等

5. 实时监控：
   - 在"实时监控"页面，可以设置关键词和阈值
   - 系统会持续监控相关话题，当讨论热度超过阈值时发出警报

6. 生成报告：
   - 在"报告管理"页面，点击"新建报告"
   - 选择要包含的分析结果和时间范围
   - 点击"生成报告"，系统会自动创建一份PDF格式的分析报告
   - 可以下载或直接在线预览生成的报告

7. 自定义仪表盘：
   - 在"仪表盘"页面，可以自定义显示的图表和数据
   - 拖拽不同的组件到仪表盘上
   - 设置刷新频率和数据源

8. 系统设置：
   - 在"设置"页面可以调整系统参数，如：
     - 更改密码
     - 设置邮件通知
     - 调整数据保留策略
     - 配置API访问权限等

9. 使用API：
   - 对于需要程序化访问的用户，可以使用系统提供的API
   - 在"API文档"页面查看详细的接口说明和示例代码

10. 获取帮助：
    - 点击界面右上角的"帮助"按钮，可以访问在线文档
    - 如遇到问题，可以通过"联系我们"页面提交反馈

## API文档

本项目提供了一些API端点供外部调用：

- `GET /api/hot_topics`: 获取当前热门话题
- `POST /api/start_spider`: 启动爬虫任务
- `GET /api/analysis_result`: 获取分析结果

详细的API文档请参考 `docs/api.md`。

## 测试

运行单元测试：
```
python -m unittest discover tests
```

## 部署

关于如何将本项目部署到生产环境，请参考 `docs/deployment.md`。

## 贡献指南

我们欢迎所有形式的贡献，无论是新功能、文档改进还是错误报告。请查看 `CONTRIBUTING.md` 了解更多信息。

## 常见问题

请查看我们的 [Wiki](https://github.com/yourusername/sentiment-analysis-system/wiki) 页面了解常见问题及解答。

## 版本历史

- v1.0.0 (2023-05-01): 初始版本发布
- v1.1.0 (2023-06-15): 添加实时监控功能
- v1.2.0 (2023-08-01): 优化数据分析算法，提高准确率

## 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 联系方式

如有任何问题或建议，请通过以下方式联系我们：

- 邮箱：support@example.com
- Twitter: [@SentimentAnalysisSystem](https://twitter.com/SentimentAnalysisSystem)
- 项目Issues: [GitHub Issues](https://github.com/yourusername/sentiment-analysis-system/issues)

## 致谢

感谢所有为本项目做出贡献的开发者和用户。特别感谢以下开源项目：

- Flask
- SQLAlchemy
- ECharts
- NLTK

没有这些优秀的工具，本项目将无法实现。
