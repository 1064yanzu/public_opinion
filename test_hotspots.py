#!/usr/bin/env python3
"""
测试热点数据加载
"""
import requests
import json
import sys

def test_hotspots_data():
    """测试热点数据是否正常加载"""
    print("=" * 60)
    print("测试每日热点数据加载")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        # 首先清理缓存
        print("1. 清理主页缓存...")
        try:
            response = requests.post(f"{base_url}/page/api/cache/clear", timeout=5)
            if response.status_code == 200:
                print("✅ 缓存清理成功")
            else:
                print(f"⚠️ 缓存清理失败: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 缓存清理请求失败: {str(e)}")
        
        # 访问主页获取数据
        print("\n2. 访问主页获取热点数据...")
        response = requests.get(f"{base_url}/page/", timeout=10)
        
        if response.status_code == 200:
            print("✅ 主页访问成功")
            
            # 检查响应内容中是否包含热点数据
            content = response.text
            
            # 检查是否有热点相关的HTML元素
            if 'daily_hotspots' in content:
                print("✅ 发现热点数据变量")
            else:
                print("❌ 未发现热点数据变量")
            
            if '每日热点' in content:
                print("✅ 发现热点标题")
            else:
                print("❌ 未发现热点标题")
            
            # 检查是否有具体的热点内容
            hotspot_indicators = [
                '侵华日军口述罪证',
                '外卖大战补贴升级',
                '苏超持续火爆',
                '东亚杯首战国足'
            ]
            
            found_hotspots = []
            for indicator in hotspot_indicators:
                if indicator in content:
                    found_hotspots.append(indicator)
            
            if found_hotspots:
                print(f"✅ 发现热点内容: {len(found_hotspots)}个")
                for hotspot in found_hotspots:
                    print(f"   - {hotspot}")
            else:
                print("❌ 未发现任何热点内容")
            
            # 检查图片链接
            if '/content/' in content:
                print("✅ 发现热点图片链接")
            else:
                print("❌ 未发现热点图片链接")
            
            return len(found_hotspots) > 0
            
        else:
            print(f"❌ 主页访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_hotspot_file():
    """测试热点文件是否存在和可读"""
    print("\n3. 检查热点数据文件...")
    
    import os
    import csv
    from datetime import datetime
    
    try:
        # 构建文件路径
        current_date = datetime.now().strftime('%Y%m%d')
        csv_file_name = f'{current_date}_pengpai.csv'
        file_path = f'static/content/{csv_file_name}'
        
        print(f"检查文件: {file_path}")
        
        if os.path.exists(file_path):
            print("✅ 热点文件存在")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                hotspots = list(reader)
                
            print(f"✅ 文件包含 {len(hotspots)} 条热点数据")
            
            if hotspots:
                print("热点数据示例:")
                for i, hotspot in enumerate(hotspots[:3]):
                    print(f"   {i+1}. {hotspot.get('标题', '无标题')[:50]}...")
                    print(f"      来源: {hotspot.get('发文者', '未知')}")
                    print(f"      链接: {hotspot.get('链接', '无链接')[:50]}...")
                    print()
            
            return True
        else:
            print(f"❌ 热点文件不存在: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 检查热点文件失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始测试每日热点功能...")
    
    # 测试文件
    file_ok = test_hotspot_file()
    
    # 测试数据加载
    data_ok = test_hotspots_data()
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    if file_ok and data_ok:
        print("🎉 热点功能测试全部通过！")
        print("每日热点应该正常显示在主页上。")
        return True
    elif file_ok:
        print("⚠️ 热点文件正常，但页面显示有问题")
        print("建议检查模板渲染和缓存机制。")
        return False
    else:
        print("❌ 热点文件或数据加载有问题")
        print("建议检查文件路径和数据获取逻辑。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
