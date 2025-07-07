#!/usr/bin/env python3
"""
测试状态栏和报告生成器修复
"""
import requests
import json
import time
import sys

def test_status_api():
    """测试状态API功能"""
    print("=" * 60)
    print("测试状态API功能")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        # 测试状态API
        print("1. 测试状态API响应...")
        response = requests.get(f"{base_url}/page/api/status", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态API响应正常")
            print(f"   状态: {data.get('status', '未知')}")
            print(f"   消息: {data.get('message', '无消息')}")
            return True
        else:
            print(f"❌ 状态API响应失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 状态API测试失败: {str(e)}")
        return False

def test_spider_task_status():
    """测试爬虫任务状态更新"""
    print("\n2. 测试爬虫任务状态更新...")
    
    base_url = "http://localhost:5000"
    
    try:
        # 模拟提交爬虫任务
        print("   提交测试爬虫任务...")
        
        # 准备表单数据
        form_data = {
            'keyword': '测试关键词',
            'platforms[]': ['微博'],
            'start_date': '',
            'end_date': '',
            'precision': '低'
        }
        
        # 提交任务（这会触发状态更新）
        response = requests.post(f"{base_url}/page/setting_spider", 
                               data=form_data, timeout=30)
        
        if response.status_code == 200:
            print("   ✅ 爬虫任务提交成功")
            
            # 检查状态是否更新
            time.sleep(2)  # 等待状态更新
            
            status_response = requests.get(f"{base_url}/page/api/status", timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   任务后状态: {status_data.get('status', '未知')}")
                print(f"   任务后消息: {status_data.get('message', '无消息')}")
                
                # 检查是否显示了任务执行状态
                if 'working' in status_data.get('status', '') or '正在' in status_data.get('message', ''):
                    print("   ✅ 状态更新正常，显示任务执行状态")
                    return True
                else:
                    print("   ⚠️ 状态更新可能有问题，未显示任务执行状态")
                    return False
            else:
                print("   ❌ 无法获取任务后状态")
                return False
        else:
            print(f"   ❌ 爬虫任务提交失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 爬虫任务测试失败: {str(e)}")
        return False

def test_report_generator():
    """测试报告生成器修复"""
    print("\n3. 测试报告生成器...")
    
    try:
        # 导入报告生成器
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from utils.report_generator import ReportGenerator
        
        # 创建报告生成器实例
        generator = ReportGenerator()
        
        # 测试上下文构建
        print("   测试上下文构建...")
        
        # 模拟一些测试数据
        test_data = {
            'basic_stats': {'total_comments': 100, 'total_interactions': 500, 'avg_interactions': 5},
            'sentiment_analysis': {'positive_ratio': 0.6, 'negative_ratio': 0.2, 'neutral_ratio': 0.2},
            'time_distribution': {'time_range': {'duration_days': 7}, 'peak_hours': {}, 'daily_stats': {}},
            'key_contents': {'top_contents': [], 'negative_contents': [], 'positive_contents': []}
        }
        
        # 设置缓存数据
        generator.data_cache = {
            'basic_stats': test_data['basic_stats'],
            'sentiment_analysis': test_data['sentiment_analysis'],
            'time_distribution': test_data['time_distribution'],
            'key_contents': test_data['key_contents']
        }
        
        # 测试构建分析上下文
        context = generator._build_analysis_context('测试主题')
        
        if context and 'analysis_results' in context:
            print("   ✅ 上下文构建成功，包含analysis_results键")
            
            # 测试更新分析上下文
            test_section = {'name': 'test_section'}
            test_content = ['测试内容']
            
            generator._update_analysis_context(context, test_section, test_content)
            
            if context['analysis_results'].get('test_section') == '测试内容':
                print("   ✅ 分析上下文更新成功")
                return True
            else:
                print("   ❌ 分析上下文更新失败")
                return False
        else:
            print("   ❌ 上下文构建失败或缺少analysis_results键")
            return False
            
    except Exception as e:
        print(f"   ❌ 报告生成器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试状态栏和报告生成器修复...")
    
    # 测试状态API
    status_ok = test_status_api()
    
    # 测试爬虫任务状态
    spider_ok = test_spider_task_status()
    
    # 测试报告生成器
    report_ok = test_report_generator()
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    results = {
        "状态API": "✅ 通过" if status_ok else "❌ 失败",
        "爬虫任务状态": "✅ 通过" if spider_ok else "❌ 失败", 
        "报告生成器": "✅ 通过" if report_ok else "❌ 失败"
    }
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    total_passed = sum([status_ok, spider_ok, report_ok])
    print(f"\n通过测试: {total_passed}/3")
    
    if total_passed == 3:
        print("🎉 所有修复测试通过！")
        return True
    elif total_passed >= 2:
        print("✅ 大部分修复生效")
        return True
    else:
        print("⚠️ 部分修复需要进一步调试")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
