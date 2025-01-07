import os
import sys
import platform
import logging
from datetime import datetime

def init_system():
    """初始化系统环境"""
    try:
        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 需要创建的目录
        directories = [
            'logs',
            'persistent_data',
            'temp_data',
            'backups',
            'static/content',
            'static/assets/images'
        ]
        
        # 创建必要的目录
        for dir_name in directories:
            dir_path = os.path.join(root_dir, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"创建目录: {dir_path}")
                
        # 在Linux环境下设置权限
        if platform.system().lower() == 'linux':
            for dir_name in directories:
                dir_path = os.path.join(root_dir, dir_name)
                os.system(f'chmod -R 755 {dir_path}')
                print(f"设置目录权限: {dir_path}")
                
        # 创建空的数据文件
        data_file = os.path.join(root_dir, 'persistent_data', 'all_any.csv')
        if not os.path.exists(data_file):
            with open(data_file, 'w', encoding='utf-8') as f:
                f.write("微博作者,微博内容,发布时间,转发数,评论数,点赞数,省份,url\n")
            print(f"创建数据文件: {data_file}")
            
        print("系统初始化完成！")
        return True
        
    except Exception as e:
        print(f"系统初始化失败: {str(e)}")
        return False

if __name__ == '__main__':
    init_system() 