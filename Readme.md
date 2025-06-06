# 舆情分析系统

## 项目简介
本项目是一个基于Python Flask框架开发的舆情分析系统，用于收集、分析和可视化社交媒体上的舆情数据。

## 功能特性
- 数据采集：支持从微博等平台采集数据
- 数据分析：支持文本分析、情感分析、热点发现等
- 数据可视化：使用图表展示分析结果
- 实时监控：支持实时舆情监控和预警
- 报告生成：自动生成分析报告

## 技术栈
- 后端：Python Flask
- 前端：HTML、CSS、JavaScript
- 数据库：SQLite
- 数据分析：jieba、snownlp等
- 可视化：Echarts

## 安装说明
1. 克隆项目
```bash
git clone https://gitee.com/scns_eat/opinion.git
cd opinion
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行项目
```bash
python app.py
```

## 项目结构
```
├── app.py              # 主程序入口
├── config.py           # 配置文件
├── requirements.txt    # 项目依赖
├── static/            # 静态文件目录
├── templates/         # 模板文件目录
├── utils/            # 工具函数
└── views/            # 视图函数
```

## 更新日志
### 2024-01-14
- 初始化项目
- 完成基础框架搭建
- 添加数据采集模块
- 添加数据分析模块
- 添加可视化展示

## 贡献者
- 傻吃苶睡 (@scns_eat)

## 许可证
MIT License
