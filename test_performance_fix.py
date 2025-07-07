#!/usr/bin/env python3
"""
性能修复测试脚本
"""
import requests
import time
import sys

def test_page_load_speed(url, test_name, expected_max_time=5.0):
    """测试页面加载速度"""
    print(f"\n测试: {test_name}")
    print(f"URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()
        
        load_time = end_time - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"加载时间: {load_time:.2f}秒")
        
        if response.status_code == 200:
            if load_time <= expected_max_time:
                print(f"✅ 性能测试通过 (≤{expected_max_time}秒)")
                return True
            else:
                print(f"⚠️ 性能测试警告 (>{expected_max_time}秒)")
                return False
        else:
            print(f"❌ 页面加载失败")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时 (>10秒)")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False

def test_api_response_speed(url, test_name, expected_max_time=2.0):
    """测试API响应速度"""
    print(f"\n测试: {test_name}")
    print(f"URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response_time:.2f}秒")
        
        if response.status_code == 200:
            if response_time <= expected_max_time:
                print(f"✅ API性能测试通过 (≤{expected_max_time}秒)")
                return True
            else:
                print(f"⚠️ API性能测试警告 (>{expected_max_time}秒)")
                return False
        else:
            print(f"❌ API请求失败")
            return False
            
    except Exception as e:
        print(f"❌ API请求失败: {str(e)}")
        return False

def test_cache_effectiveness():
    """测试缓存效果"""
    print(f"\n测试: 缓存效果验证")
    
    base_url = "http://localhost:5000"
    
    # 第一次请求（冷启动）
    print("第一次请求（冷启动）...")
    start_time = time.time()
    try:
        response1 = requests.get(f"{base_url}/page/", timeout=10)
        first_load_time = time.time() - start_time
        print(f"首次加载时间: {first_load_time:.2f}秒")
    except Exception as e:
        print(f"首次请求失败: {str(e)}")
        return False
    
    # 等待1秒
    time.sleep(1)
    
    # 第二次请求（应该使用缓存）
    print("第二次请求（应该使用缓存）...")
    start_time = time.time()
    try:
        response2 = requests.get(f"{base_url}/page/", timeout=10)
        second_load_time = time.time() - start_time
        print(f"缓存加载时间: {second_load_time:.2f}秒")
    except Exception as e:
        print(f"第二次请求失败: {str(e)}")
        return False
    
    # 分析缓存效果
    if second_load_time < first_load_time * 0.8:  # 缓存应该至少快20%
        improvement = ((first_load_time - second_load_time) / first_load_time) * 100
        print(f"✅ 缓存效果良好，性能提升 {improvement:.1f}%")
        return True
    else:
        print(f"⚠️ 缓存效果不明显")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("Flask舆情监测系统 - 性能修复验证测试")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    tests = [
        # 基础连接测试
        (f"{base_url}", "应用基础连接", 3.0),
        
        # 主页加载测试
        (f"{base_url}/page/", "主页加载速度", 5.0),
        
        # API响应测试
        (f"{base_url}/page/api/status", "状态API响应", 1.0),
        
        # 爬虫设置页面
        (f"{base_url}/page/setting_spider", "爬虫设置页面", 4.0),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    # 执行页面加载测试
    for url, test_name, max_time in tests:
        if test_page_load_speed(url, test_name, max_time):
            passed_tests += 1
    
    # 执行缓存效果测试
    if test_cache_effectiveness():
        passed_tests += 1
    total_tests += 1
    
    # 测试结果总结
    print(f"\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"通过测试: {passed_tests}/{total_tests}")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 所有性能测试通过！系统性能优化成功！")
        return True
    elif passed_tests >= total_tests * 0.8:
        print("✅ 大部分测试通过，系统性能良好")
        return True
    else:
        print("⚠️ 部分测试未通过，需要进一步优化")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
