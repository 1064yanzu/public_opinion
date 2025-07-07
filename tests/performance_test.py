"""
性能测试脚本 - 验证优化效果
"""
import time
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cache_manager import cached, clear_cache, get_cache_stats
from utils.csv_optimizer import csv_optimizer
from utils.performance_monitor import performance_monitor, monitor_performance, get_performance_report
from model.nlp import batch_analyze_sentiment, analyze_sentiment


def create_test_data(num_rows=1000):
    """创建测试数据"""
    print(f"创建测试数据，行数: {num_rows}")
    
    # 模拟微博内容
    sample_texts = [
        "今天天气真好，心情很棒！",
        "这个产品质量太差了，很失望",
        "一般般吧，没什么特别的",
        "非常满意这次的服务体验",
        "价格有点贵，但是质量还可以",
        "客服态度很好，解决问题很及时",
        "物流速度太慢了，等了很久",
        "包装很精美，产品也很不错",
        "性价比很高，推荐购买",
        "使用体验一般，有待改进"
    ]
    
    data = {
        '微博内容': np.random.choice(sample_texts, num_rows),
        '转发数': np.random.randint(0, 1000, num_rows),
        '评论数': np.random.randint(0, 500, num_rows),
        '点赞数': np.random.randint(0, 2000, num_rows),
        '发布时间': pd.date_range('2024-01-01', periods=num_rows, freq='H')
    }
    
    df = pd.DataFrame(data)
    test_file = 'tests/test_data.csv'
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    df.to_csv(test_file, index=False, encoding='utf-8-sig')
    
    print(f"测试数据已保存到: {test_file}")
    return test_file


def test_csv_performance():
    """测试CSV读写性能"""
    print("\n=== CSV读写性能测试 ===")
    
    # 创建测试数据
    test_file = create_test_data(5000)
    
    # 测试原生pandas读取
    start_time = time.time()
    df_pandas = pd.read_csv(test_file)
    pandas_time = time.time() - start_time
    print(f"Pandas读取时间: {pandas_time:.3f}秒")
    
    # 测试优化后的读取
    start_time = time.time()
    df_optimized = csv_optimizer.read_csv_optimized(test_file)
    optimized_time = time.time() - start_time
    print(f"优化读取时间: {optimized_time:.3f}秒")
    
    # 计算性能提升
    if pandas_time > 0:
        improvement = ((pandas_time - optimized_time) / pandas_time) * 100
        print(f"性能提升: {improvement:.1f}%")
    
    # 测试写入性能
    start_time = time.time()
    csv_optimizer.write_csv_optimized(df_optimized, 'tests/test_output.csv')
    write_time = time.time() - start_time
    print(f"优化写入时间: {write_time:.3f}秒")
    
    # 清理测试文件
    for file in [test_file, 'tests/test_output.csv']:
        if os.path.exists(file):
            os.remove(file)


def test_sentiment_analysis_performance():
    """测试情感分析性能"""
    print("\n=== 情感分析性能测试 ===")
    
    # 准备测试文本
    test_texts = [
        "今天天气真好，心情很棒！",
        "这个产品质量太差了，很失望",
        "一般般吧，没什么特别的",
        "非常满意这次的服务体验",
        "价格有点贵，但是质量还可以"
    ] * 200  # 1000条文本
    
    print(f"测试文本数量: {len(test_texts)}")
    
    # 测试单条分析
    start_time = time.time()
    single_results = []
    for text in test_texts[:100]:  # 只测试100条，避免太慢
        result = analyze_sentiment(text)
        single_results.append(result)
    single_time = time.time() - start_time
    print(f"单条分析时间(100条): {single_time:.3f}秒")
    
    # 测试批量分析
    start_time = time.time()
    batch_results = batch_analyze_sentiment(test_texts)
    batch_time = time.time() - start_time
    print(f"批量分析时间(1000条): {batch_time:.3f}秒")
    
    # 计算性能提升（按比例）
    estimated_single_time = single_time * 10  # 估算1000条的时间
    if estimated_single_time > 0:
        improvement = ((estimated_single_time - batch_time) / estimated_single_time) * 100
        print(f"批量处理性能提升: {improvement:.1f}%")


def test_cache_performance():
    """测试缓存性能"""
    print("\n=== 缓存性能测试 ===")
    
    # 清空缓存
    clear_cache()
    
    @cached(ttl=300, key_prefix="test")
    def expensive_operation(n):
        """模拟耗时操作"""
        time.sleep(0.1)  # 模拟100ms的计算时间
        return n * n
    
    # 测试首次调用（无缓存）
    start_time = time.time()
    result1 = expensive_operation(10)
    first_call_time = time.time() - start_time
    print(f"首次调用时间: {first_call_time:.3f}秒")
    
    # 测试缓存命中
    start_time = time.time()
    result2 = expensive_operation(10)
    cached_call_time = time.time() - start_time
    print(f"缓存命中时间: {cached_call_time:.3f}秒")
    
    # 验证结果一致性
    assert result1 == result2, "缓存结果不一致"
    
    # 计算性能提升
    if first_call_time > 0:
        improvement = ((first_call_time - cached_call_time) / first_call_time) * 100
        print(f"缓存性能提升: {improvement:.1f}%")
    
    # 显示缓存统计
    stats = get_cache_stats()
    print(f"缓存统计: {stats}")


@monitor_performance('test_function')
def test_performance_monitoring():
    """测试性能监控"""
    print("\n=== 性能监控测试 ===")
    
    # 模拟一些操作
    time.sleep(0.1)
    data = [i for i in range(1000)]
    result = sum(data)
    
    return result


def test_async_task_manager():
    """测试异步任务管理器"""
    print("\n=== 异步任务管理器测试 ===")

    from utils.async_task_manager import task_manager

    def test_task(n, delay=0.1):
        """测试任务函数"""
        time.sleep(delay)
        return n * n

    # 提交多个任务
    task_ids = []
    for i in range(5):
        task_id = task_manager.submit_task(test_task, i, delay=0.2)
        task_ids.append(task_id)

    print(f"提交了 {len(task_ids)} 个任务")

    # 等待任务完成
    results = []
    for task_id in task_ids:
        try:
            result = task_manager.get_task_result(task_id, timeout=5)
            results.append(result)
            print(f"任务 {task_id} 结果: {result}")
        except Exception as e:
            print(f"任务 {task_id} 失败: {str(e)}")

    print(f"完成任务数: {len(results)}")

    # 获取任务统计
    all_tasks = task_manager.get_all_tasks()
    print(f"任务统计: 总任务数={len(all_tasks)}")


def test_network_optimizer():
    """测试网络优化器"""
    print("\n=== 网络优化器测试 ===")

    from utils.network_optimizer import network_optimizer

    # 测试单个请求
    test_url = "https://httpbin.org/json"
    start_time = time.time()
    result = network_optimizer.request(test_url)
    request_time = time.time() - start_time

    print(f"单个请求耗时: {request_time:.3f}秒")
    print(f"请求成功: {result is not None}")

    # 测试批量请求
    urls = [
        {"url": "https://httpbin.org/json"},
        {"url": "https://httpbin.org/uuid"},
        {"url": "https://httpbin.org/ip"}
    ]

    start_time = time.time()
    results = network_optimizer.batch_request(urls, max_workers=3)
    batch_time = time.time() - start_time

    success_count = sum(1 for r in results if r is not None)
    print(f"批量请求耗时: {batch_time:.3f}秒")
    print(f"成功请求数: {success_count}/{len(urls)}")

    # 获取网络统计
    stats = network_optimizer.get_stats()
    print(f"网络统计: {stats}")


def test_data_pipeline():
    """测试数据处理流水线"""
    print("\n=== 数据处理流水线测试 ===")

    from utils.data_pipeline import DataPipeline

    # 创建测试数据
    test_data = [
        {"content": "这是一个测试文本", "score": 10},
        {"content": "另一个测试内容", "score": 20},
        {"content": "第三个测试数据", "score": 30}
    ]

    # 定义处理函数
    def validate_data(data):
        return [item for item in data if item.get('content')]

    def transform_data(data):
        for item in data:
            item['processed'] = True
            item['length'] = len(item.get('content', ''))
        return data

    def aggregate_data(data):
        total_score = sum(item.get('score', 0) for item in data)
        return {"total_items": len(data), "total_score": total_score, "data": data}

    # 创建流水线
    pipeline = DataPipeline()
    pipeline.add_step('验证', validate_data)
    pipeline.add_step('转换', transform_data)
    pipeline.add_step('聚合', aggregate_data)

    # 执行流水线
    start_time = time.time()
    result = pipeline.execute(test_data)
    pipeline_time = time.time() - start_time

    print(f"流水线执行耗时: {pipeline_time:.3f}秒")
    print(f"处理结果: {result}")

    # 获取流水线统计
    stats = pipeline.get_stats()
    print(f"流水线统计: {stats}")


def test_advanced_cache():
    """测试高级缓存系统"""
    print("\n=== 高级缓存系统测试 ===")

    from utils.advanced_cache import advanced_cache

    # 清空缓存
    advanced_cache.clear()

    # 测试多层缓存
    test_data = {"key1": "value1", "key2": [1, 2, 3, 4, 5]}

    # 第一次访问（缓存未命中）
    start_time = time.time()
    advanced_cache.set("test_key", test_data)
    set_time = time.time() - start_time
    print(f"缓存设置时间: {set_time:.3f}秒")

    # 第二次访问（L1缓存命中）
    start_time = time.time()
    result1 = advanced_cache.get("test_key")
    l1_time = time.time() - start_time
    print(f"L1缓存命中时间: {l1_time:.3f}秒")

    # 清空L1缓存，测试L2缓存
    advanced_cache.l1_cache.clear()

    start_time = time.time()
    result2 = advanced_cache.get("test_key")
    l2_time = time.time() - start_time
    print(f"L2缓存命中时间: {l2_time:.3f}秒")

    # 验证数据一致性
    assert result1 == test_data, "L1缓存数据不一致"
    assert result2 == test_data, "L2缓存数据不一致"

    # 获取缓存统计
    stats = advanced_cache.get_stats()
    print(f"高级缓存统计: {stats}")


def test_monitoring_alerts():
    """测试监控告警系统"""
    print("\n=== 监控告警系统测试 ===")

    from utils.monitoring_alerts import alert_manager

    # 手动触发告警检查
    alerts = alert_manager.check_alerts()
    print(f"触发的告警数量: {len(alerts)}")

    if alerts:
        for alert in alerts:
            print(f"告警: {alert['rule_name']} - {alert['severity']}")

    # 获取告警统计
    stats = alert_manager.get_alert_stats()
    print(f"告警统计: {stats}")

    # 获取告警历史
    history = alert_manager.get_alert_history(5)
    print(f"最近告警历史: {len(history)} 条")


def test_smart_preprocessor():
    """测试智能预处理器"""
    print("\n=== 智能预处理器测试 ===")

    from utils.smart_preprocessor import smart_preprocessor

    # 创建测试数据
    test_data = [
        {
            "微博内容": "今天天气真好！@某人 #话题# http://example.com 😊",
            "转发数": "100",
            "评论数": "50",
            "点赞数": "200",
            "发布时间": "2024-01-01"
        },
        {
            "微博内容": "这是另一条测试微博内容",
            "转发数": "abc",  # 错误的数值格式
            "评论数": "30",
            "点赞数": "150"
            # 缺少发布时间
        }
    ]

    # 执行预处理
    start_time = time.time()
    result = smart_preprocessor.preprocess_data(test_data, data_type='weibo')
    process_time = time.time() - start_time

    print(f"预处理耗时: {process_time:.3f}秒")
    print(f"处理结果: {len(result['processed_data'])} 条记录")

    if result['validation_result']:
        validation = result['validation_result']
        print(f"验证结果: 有效={validation['valid_count']}, 无效={validation['invalid_count']}")
        print(f"成功率: {validation['success_rate']:.1f}%")

    # 获取预处理统计
    stats = smart_preprocessor.get_stats()
    print(f"预处理统计: {stats}")


def test_frontend_optimization():
    """测试前端优化功能"""
    print("\n=== 前端优化功能测试 ===")

    from utils.frontend_optimizer import static_optimizer, cdn_optimizer

    # 获取静态资源优化统计
    static_stats = static_optimizer.get_stats()
    print(f"静态资源优化统计: {static_stats}")

    # 测试CDN URL生成
    jquery_url = cdn_optimizer.get_cdn_url('jquery')
    bootstrap_css = cdn_optimizer.get_cdn_url('bootstrap', 'css')

    print(f"jQuery CDN URL: {jquery_url}")
    print(f"Bootstrap CSS URL: {bootstrap_css}")

    # 测试CDN HTML生成
    jquery_html = cdn_optimizer.generate_cdn_html('jquery')
    print(f"jQuery HTML: {jquery_html[:100]}...")


def run_all_tests():
    """运行所有性能测试"""
    print("开始性能测试...")
    print(f"测试时间: {datetime.now()}")

    try:
        # 第一阶段测试
        test_csv_performance()
        test_sentiment_analysis_performance()
        test_cache_performance()

        # 第二阶段测试
        test_async_task_manager()
        test_network_optimizer()
        test_data_pipeline()

        # 第三阶段测试
        test_advanced_cache()
        test_monitoring_alerts()
        test_smart_preprocessor()
        test_frontend_optimization()

        # 性能监控测试
        result = test_performance_monitoring()
        print(f"\n性能监控测试结果: {result}")

        # 获取性能报告
        print("\n=== 系统性能报告 ===")
        report = get_performance_report()

        print(f"CPU使用率: {report['system']['cpu']['percent']:.1f}%")
        print(f"内存使用率: {report['system']['memory']['percent']:.1f}%")
        print(f"进程内存: {report['system']['memory']['process_rss_mb']:.1f}MB")
        print(f"缓存大小: {report['system']['cache']['size']}")

        print("\n优化建议:")
        for recommendation in report['recommendations']:
            print(f"- {recommendation}")

        print("\n✅ 所有性能测试完成！")

    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
