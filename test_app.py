#!/usr/bin/env python3
"""
测试Flask应用是否正常运行
"""
import requests
import time
import sys

def test_app():
    """测试应用是否正常运行"""
    base_url = "http://localhost:5000"
    
    # 等待应用启动
    print("等待应用启动...")
    time.sleep(3)
    
    try:
        # 测试健康检查端点
        print("测试健康检查端点...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到应用: {str(e)}")
        return False
    
    try:
        # 测试主页
        print("测试主页...")
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ 主页访问成功")
        else:
            print(f"❌ 主页访问失败: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 主页访问异常: {str(e)}")
    
    try:
        # 测试静态文件
        print("测试静态文件...")
        response = requests.get(f"{base_url}/test", timeout=5)
        if response.status_code == 200:
            print("✅ 测试页面访问成功")
        else:
            print(f"❌ 测试页面访问失败: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 测试页面访问异常: {str(e)}")
    
    try:
        # 测试性能监控
        print("测试性能监控...")
        response = requests.get(f"{base_url}/api/performance/stats", timeout=5)
        if response.status_code == 200:
            print("✅ 性能监控正常")
        else:
            print(f"❌ 性能监控失败: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 性能监控异常: {str(e)}")
    
    return True

if __name__ == "__main__":
    print("开始测试Flask应用...")
    success = test_app()
    if success:
        print("\n🎉 应用测试完成！")
    else:
        print("\n❌ 应用测试失败！")
        sys.exit(1)
