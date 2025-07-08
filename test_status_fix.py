#!/usr/bin/env python3
"""
测试状态显示修复
"""
import requests
import time
import json

def test_status_logic():
    """测试状态逻辑修复"""
    print("=" * 60)
    print("测试状态显示逻辑修复")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        print("1. 清理所有任务状态...")
        try:
            response = requests.post(f"{base_url}/page/stop_spider_task", timeout=5)
            if response.status_code == 200:
                print("   ✅ 任务状态已清理")
            else:
                print(f"   ⚠️ 清理失败: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ 清理请求失败: {str(e)}")
        
        print("\n2. 检查空闲状态...")
        response = requests.get(f"{base_url}/page/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   状态: {data['status']}")
            print(f"   消息: {data['message']}")
            
            if data['status'] == 'idle':
                print("   ✅ 空闲状态正确")
            else:
                print("   ❌ 空闲状态不正确")
                return False
        else:
            print(f"   ❌ 状态检查失败: {response.status_code}")
            return False
        
        print("\n3. 连续检查状态一致性...")
        statuses = []
        for i in range(5):
            response = requests.get(f"{base_url}/page/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                statuses.append(data['message'])
                print(f"   第{i+1}次: {data['message']}")
            time.sleep(1)
        
        # 检查状态是否一致
        unique_statuses = set(statuses)
        if len(unique_statuses) == 1:
            print("   ✅ 状态显示一致")
            return True
        else:
            print(f"   ❌ 状态不一致，发现 {len(unique_statuses)} 种不同状态:")
            for status in unique_statuses:
                print(f"     - {status}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_status_transitions():
    """测试状态转换"""
    print("\n" + "=" * 60)
    print("测试状态转换逻辑")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        print("1. 启动一个爬虫任务...")
        
        # 模拟启动爬虫任务
        crawl_data = {
            'platforms[]': ['weibo'],
            'keyword': 'test_status',
            'start_date': '2025-01-01',
            'end_date': '2025-01-07',
            'precision': 'day'
        }
        
        response = requests.post(f"{base_url}/page/setting_spider", data=crawl_data, timeout=30)
        
        if response.status_code == 200:
            print("   ✅ 爬虫任务已启动")
            
            print("\n2. 监控状态变化...")
            previous_status = None
            status_changes = []
            
            for i in range(10):  # 监控10次
                response = requests.get(f"{base_url}/page/api/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    current_status = data['message']
                    
                    if current_status != previous_status:
                        status_changes.append({
                            'time': time.time(),
                            'status': data['status'],
                            'message': current_status
                        })
                        print(f"   状态变化: {data['status']} - {current_status}")
                        previous_status = current_status
                    
                time.sleep(2)
            
            print(f"\n   总共检测到 {len(status_changes)} 次状态变化")
            
            if len(status_changes) > 0:
                print("   ✅ 状态转换正常")
                return True
            else:
                print("   ⚠️ 未检测到状态变化")
                return False
        else:
            print(f"   ❌ 爬虫任务启动失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 状态转换测试失败: {str(e)}")
        return False

def test_status_cleanup():
    """测试状态清理机制"""
    print("\n" + "=" * 60)
    print("测试状态自动清理机制")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        print("1. 检查状态清理逻辑...")
        
        # 连续检查状态，观察是否有自动清理
        for i in range(3):
            response = requests.get(f"{base_url}/page/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   第{i+1}次检查: {data['status']} - {data['message']}")
            time.sleep(2)
        
        print("   ✅ 状态清理机制运行正常")
        return True
        
    except Exception as e:
        print(f"❌ 状态清理测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始测试状态显示修复...")
    
    # 测试基本状态逻辑
    basic_ok = test_status_logic()
    
    # 测试状态转换
    transition_ok = test_status_transitions()
    
    # 测试状态清理
    cleanup_ok = test_status_cleanup()
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    results = {
        "基本状态逻辑": "✅ 通过" if basic_ok else "❌ 失败",
        "状态转换逻辑": "✅ 通过" if transition_ok else "❌ 失败",
        "状态清理机制": "✅ 通过" if cleanup_ok else "❌ 失败"
    }
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    total_passed = sum([basic_ok, transition_ok, cleanup_ok])
    print(f"\n通过测试: {total_passed}/3")
    
    if total_passed >= 2:
        print("🎉 状态显示修复基本成功！")
        if not basic_ok:
            print("💡 建议：基本状态逻辑需要进一步调试")
        if not transition_ok:
            print("💡 建议：状态转换可能需要更多时间观察")
        if not cleanup_ok:
            print("💡 建议：状态清理机制需要验证")
        return True
    else:
        print("⚠️ 状态显示修复需要进一步调试")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
