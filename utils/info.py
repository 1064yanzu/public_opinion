# 导入必要的库
import pandas as pd
import os
from utils.common import get_persistent_file_path
import traceback

def fenxi():
    """分析数据文件并返回统计信息"""
    try:
        # 获取数据文件路径
        data_file = get_persistent_file_path('all', 'any')
        print(f"正在读取数据文件: {data_file}")
        
        # 检查文件是否存在
        if not os.path.exists(data_file):
            print(f"数据文件不存在: {data_file}")
            return 0, 0, 0, 0
            
        # 尝试不同编码读取文件
        for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
            try:
                df = pd.read_csv(data_file, encoding=encoding)
                print(f"使用 {encoding} 编码成功读取文件")
                break
            except Exception as e:
                print(f"使用 {encoding} 编码读取失败: {str(e)}")
                continue
        else:
            print("所有编码尝试均失败")
            return 0, 0, 0, 0
            
        print(f"成功读取数据文件，行数: {len(df)}")
        print(f"列名: {df.columns.tolist()}")
        
        if len(df) == 0:
            return 0, 0, 0, 0
            
        # 定义可能的列名映射
        column_mappings = {
            'author': ['微博作者', '作者', 'author', '用户名', 'username'],
            'province': ['省份', '地区', 'province', 'location', '位置'],
            'shares': ['转发数', '分享数', 'shares', 'repost_count'],
            'comments': ['评论数', 'comments', 'comment_count'],
            'likes': ['点赞数', '赞数', 'likes', 'like_count']
        }

        # 获取实际的列名
        actual_columns = {}
        for key, possible_names in column_mappings.items():
            for name in possible_names:
                if name in df.columns:
                    actual_columns[key] = name
                    break
            if key not in actual_columns:
                print(f"未找到{key}对应的列名")
                actual_columns[key] = None
            
        # 计算统计数据
        row_count = len(df)  # 总信息数量
        
        # 获取评论者数量
        unique_user_count = df[actual_columns['author']].nunique() if actual_columns['author'] else 0
        
        # 获取IP地址数
        unique_ip_count = df[actual_columns['province']].nunique() if actual_columns['province'] else 0
        
        # 计算热度值
        try:
            # 准备数值列
            shares = pd.to_numeric(df[actual_columns['shares']], errors='coerce').fillna(0) if actual_columns['shares'] else 0
            comments = pd.to_numeric(df[actual_columns['comments']], errors='coerce').fillna(0) if actual_columns['comments'] else 0
            likes = pd.to_numeric(df[actual_columns['likes']], errors='coerce').fillna(0) if actual_columns['likes'] else 0
            
            # 计算热度
            total_heat_value = int((
                shares.sum() * 0.4 + 
                comments.sum() * 0.3 + 
                likes.sum() * 0.3
            ) / 100)
            
        except Exception as e:
            print(f"计算热度值时出错: {str(e)}")
            total_heat_value = 0
            
        print(f"统计结果: 用户数={unique_user_count}, 热度={total_heat_value}, IP数={unique_ip_count}, 总数={row_count}")
        return unique_user_count, total_heat_value, unique_ip_count, row_count
        
    except Exception as e:
        print(f"fenxi函数执行出错: {str(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        return 0, 0, 0, 0

if __name__ == '__main__':
    fenxi()