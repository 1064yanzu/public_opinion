import os
from functools import lru_cache

# API配置 - 从环境变量获取，提供默认值
ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY", "011f3b2503b3df17f792d2d0512fc175.eE53OpK9lcrPjMBr")

# 性能优化配置
PERFORMANCE_CONFIG = {
    # 缓存配置
    'cache_enabled': os.environ.get('CACHE_ENABLED', 'true').lower() == 'true',
    'cache_ttl': int(os.environ.get('CACHE_TTL', '3600')),  # 缓存过期时间（秒）
    'max_cache_size': int(os.environ.get('MAX_CACHE_SIZE', '1000')),  # 最大缓存条目数

    # 批处理配置
    'batch_size': int(os.environ.get('BATCH_SIZE', '100')),  # 批处理大小
    'memory_limit_mb': int(os.environ.get('MEMORY_LIMIT_MB', '512')),  # 内存限制（MB）

    # 并发配置
    'max_workers': int(os.environ.get('MAX_WORKERS', '4')),  # 最大工作线程数
    'max_concurrent_requests': int(os.environ.get('MAX_CONCURRENT_REQUESTS', '10')),  # 最大并发请求数
    'enable_concurrent_crawling': os.environ.get('ENABLE_CONCURRENT_CRAWLING', 'true').lower() == 'true',

    # 网络配置
    'request_timeout': int(os.environ.get('REQUEST_TIMEOUT', '30')),  # 请求超时时间（秒）
    'request_retry': int(os.environ.get('REQUEST_RETRY', '3')),  # 请求重试次数
    'request_delay': float(os.environ.get('REQUEST_DELAY', '0.5')),  # 请求间隔（秒）

    # 数据处理配置
    'enable_data_pipeline': os.environ.get('ENABLE_DATA_PIPELINE', 'true').lower() == 'true',
    'pipeline_parallel': os.environ.get('PIPELINE_PARALLEL', 'true').lower() == 'true',

    # 监控配置
    'max_metrics': int(os.environ.get('MAX_METRICS', '1000')),  # 最大监控指标数
    'cleanup_interval_hours': int(os.environ.get('CLEANUP_INTERVAL_HOURS', '24')),  # 清理间隔（小时）
    'enable_monitoring': os.environ.get('ENABLE_MONITORING', 'true').lower() == 'true',

    # 高级缓存配置（第三阶段新增）
    'l1_cache_size': int(os.environ.get('L1_CACHE_SIZE', '500')),  # L1缓存大小
    'l1_cache_ttl': int(os.environ.get('L1_CACHE_TTL', '300')),  # L1缓存TTL（秒）
    'l2_cache_size_mb': int(os.environ.get('L2_CACHE_SIZE_MB', '100')),  # L2缓存大小（MB）
    'cache_dir': os.environ.get('CACHE_DIR', 'cache'),  # 缓存目录

    # 前端优化配置（第三阶段新增）
    'enable_compression': os.environ.get('ENABLE_COMPRESSION', 'true').lower() == 'true',
    'static_cache_max_age': int(os.environ.get('STATIC_CACHE_MAX_AGE', '86400')),  # 静态资源缓存时间（秒）

    # 告警配置（第三阶段新增）
    'email_alerts_enabled': os.environ.get('EMAIL_ALERTS_ENABLED', 'false').lower() == 'true',
    'smtp_server': os.environ.get('SMTP_SERVER', ''),
    'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
    'smtp_user': os.environ.get('SMTP_USER', ''),
    'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
    'alert_recipients': os.environ.get('ALERT_RECIPIENTS', '').split(',') if os.environ.get('ALERT_RECIPIENTS') else [],

    # 数据预处理配置（第三阶段新增）
    'stopwords_file': os.environ.get('STOPWORDS_FILE', ''),  # 停用词文件路径
    'text_cleaning_enabled': os.environ.get('TEXT_CLEANING_ENABLED', 'true').lower() == 'true',
    'data_validation_enabled': os.environ.get('DATA_VALIDATION_ENABLED', 'true').lower() == 'true',
}

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