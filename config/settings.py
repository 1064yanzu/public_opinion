# API配置
import os

# 从环境变量获取 ZHIPUAI_API_KEY，避免密钥直接写在代码中
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")


# 报告生成配置
REPORT_CONFIG = {
    'basic': {
        'summary_length': 800,
        'analysis_depth': '基础',
        'suggestion_count': 5
    },
    'standard': {
        'summary_length': 1200,
        'analysis_depth': '标准',
        'suggestion_count': 8
    },
    'deep': {
        'summary_length': 2000,
        'analysis_depth': '深度',
        'suggestion_count': 10
    }
}

# 模型配置
MODEL_CONFIG = {
    'model': 'glm-4-flash',
    'temperature': 0.3,
    'top_p': 0.7,
    'max_tokens': 4000,  # 增加token限制以获得更长的报告
}

# CSV列名映射
CSV_COLUMNS = {
    '发布时间': '发布时间',
    '微博内容': '微博内容',
    '转发数': '转发数',
    '评论数': '评论数',
    '点赞数': '点赞数',
    '省份': '省份',
    '城市': '城市',
    '用户关注粉丝数': '用户关注粉丝数'
} 