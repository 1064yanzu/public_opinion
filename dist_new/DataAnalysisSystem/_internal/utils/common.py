import os
import pandas as pd
from datetime import datetime
def get_persistent_file_path(platform, keyword):
    # 获取当前文件的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取父目录
    parent_dir = os.path.dirname(current_dir)
    
    # 构建兄弟目录的路径
    persistent_data_dir = os.path.join(parent_dir, 'persistent_data')
    
    # 确保目录存在
    if not os.path.exists(persistent_data_dir):
        os.makedirs(persistent_data_dir)
    
    # 构建文件路径
    file_name = f'{platform}_{keyword}.csv'
    return os.path.join(persistent_data_dir, file_name)

def get_temp_file_path(platform):
    """获取临时文件路径"""
    return f'{platform}_temp.csv'

def update_persistent_file(persistent_file, temp_file):
    if not os.path.exists(persistent_file):
        pd.read_csv(temp_file).to_csv(persistent_file, index=False)
    else:
        existing_df = pd.read_csv(persistent_file)
        new_df = pd.read_csv(temp_file)
        merged_df = pd.concat([existing_df, new_df]).drop_duplicates(subset='uni_id', keep='last')
        merged_df.to_csv(persistent_file, index=False)
