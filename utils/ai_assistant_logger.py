"""
AI助手日志模块 - 记录用户活动和系统事件
"""
import os
import json
import logging
from datetime import datetime
import socket
import traceback

# 配置日志
LOG_DIR = 'logs/ai_assistant'
LOG_FILE = 'ai_assistant.log'
ACTIVITY_LOG_FILE = 'activity.log'

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 配置系统日志
system_logger = logging.getLogger('ai_assistant.system')
system_logger.setLevel(logging.INFO)

# 文件处理器
file_handler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE), encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 格式化器
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 添加处理器
system_logger.addHandler(file_handler)

def log_system_event(event_type, message, error=None):
    """
    记录系统事件
    
    参数:
        event_type (str): 事件类型
        message (str): 事件消息
        error (Exception, optional): 错误对象
    """
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message
        }
        
        if error:
            log_entry['error'] = str(error)
            log_entry['traceback'] = traceback.format_exc()
        
        system_logger.info(json.dumps(log_entry, ensure_ascii=False))
    except Exception as e:
        print(f"记录系统事件失败: {str(e)}")

def log_user_activity(user_id, username, ip_address, action, message=None, response=None, additional_info=None):
    """
    记录用户活动
    
    参数:
        user_id (str): 用户ID
        username (str): 用户名
        ip_address (str): IP地址
        action (str): 活动类型
        message (str, optional): 用户消息
        response (str, optional): 系统响应
        additional_info (dict, optional): 额外信息
    """
    try:
        # 创建日志条目
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'username': username,
            'ip_address': ip_address,
            'action': action,
            'hostname': socket.gethostname()
        }
        
        if message:
            log_entry['message'] = message
        
        if response:
            # 截断过长的响应
            if len(response) > 1000:
                log_entry['response'] = response[:1000] + "... [截断]"
            else:
                log_entry['response'] = response
        
        if additional_info:
            log_entry['additional_info'] = additional_info
        
        # 写入日志文件
        with open(os.path.join(LOG_DIR, ACTIVITY_LOG_FILE), 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    except Exception as e:
        print(f"记录用户活动失败: {str(e)}")
        system_logger.error(f"记录用户活动失败: {str(e)}")

def get_client_ip(request):
    """
    获取客户端IP地址
    
    参数:
        request: Flask请求对象
    
    返回:
        str: 客户端IP地址
    """
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    elif request.environ.get('HTTP_X_REAL_IP'):
        return request.environ['HTTP_X_REAL_IP']
    else:
        return request.remote_addr
