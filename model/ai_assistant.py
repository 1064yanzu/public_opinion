"""
AI助手模块 - 处理与第三方大模型API的交互
"""
from openai import OpenAI
import os
import json
from datetime import datetime

# 尝试从.env文件加载环境变量
def load_env_file():
    """从.env文件加载环境变量"""
    try:
        env_paths = ['.env', '../.env', '../../.env']  # 尝试多个可能的路径
        for env_path in env_paths:
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            try:
                                key, value = line.split('=', 1)
                                if key and value and key not in os.environ:
                                    os.environ[key] = value
                            except ValueError:
                                pass  # 忽略格式不正确的行
                print(f"已从{env_path}文件加载环境变量")
                return True
        return False
    except Exception as e:
        print(f"加载.env文件失败: {str(e)}")
        return False

# 尝试加载环境变量
load_env_file()

# 配置API密钥和基础URL
def get_api_client():
    """获取API客户端，确保使用环境变量中的API密钥"""
    # 先检查环境变量
    api_key = os.environ.get("SILICONFLOW_API_KEY")

    # 如果环境变量中没有，尝试从配置文件读取
    if not api_key:
        config_paths = ['config.json', 'config/config.json', '../config/config.json']
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        api_key = config.get('SILICONFLOW_API_KEY')
                        if api_key:
                            print(f"从{config_path}读取到API密钥")
                            break
                except Exception as e:
                    print(f"读取配置文件{config_path}失败: {str(e)}")

    # 如果还是没有找到API密钥，抛出错误
    if not api_key:
        raise ValueError("无法获取API密钥，请设置环境变量 SILICONFLOW_API_KEY 或在配置文件中指定")

    base_url = os.environ.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")

    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )

# 从环境变量或配置文件中获取模型ID
def get_model_id():
    """从环境变量或配置文件中获取模型ID"""
    # 默认模型ID
    default_model_id = "ft:LoRA/Qwen/Qwen2.5-32B-Instruct:uy4pgkdhjs:yuqing:dkzxjcayvpokexfohjob"

    # 先从环境变量中获取
    model_id = os.environ.get("SILICONFLOW_MODEL_ID")

    # 如果环境变量中没有，尝试从配置文件读取
    if not model_id:
        config_paths = ['config.json', 'config/config.json', '../config/config.json']
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        model_id = config.get('SILICONFLOW_MODEL_ID')
                        if model_id:
                            break
                except Exception:
                    pass

    # 如果还是没有找到，使用默认值
    return model_id or default_model_id

def get_chat_response(message, chat_history=None):
    """
    获取AI助手的回复

    参数:
        message (str): 用户输入的消息
        chat_history (list): 聊天历史记录

    返回:
        str: AI助手的回复
    """
    # 准备消息列表
    messages = []

    # 不使用系统提示词

    # 添加聊天历史记录（如果有）
    if chat_history:
        for entry in chat_history:
            if 'user' in entry and entry['user'].strip():
                messages.append({"role": "user", "content": entry['user']})
            if 'ai' in entry and entry['ai'].strip():
                messages.append({"role": "assistant", "content": entry['ai']})

    # 添加当前用户消息
    messages.append({"role": "user", "content": message})

    try:
        # 获取API客户端和模型ID
        client = get_api_client()
        model_id = get_model_id()

        # 调用API获取回复
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=True,
            max_tokens=4096,
            # temperature=0.5,  # 控制创造性，值越低回答越保守
            # top_p=0.95        # 控制输出多样性
        )

        # 收集流式响应
        collected_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                collected_response += chunk.choices[0].delta.content

        return collected_response

    except Exception as e:
        print(f"API调用失败: {str(e)}")
        return f"抱歉，在处理您的请求时遇到了问题。错误信息: {str(e)}"

def verify_access_password(password):
    """
    验证访问密码

    参数:
        password (str): 用户输入的密码

    返回:
        bool: 密码是否正确
    """
    # 默认密码
    default_password = "yuqing2024"

    # 先从环境变量中获取
    correct_password = os.environ.get("AI_ASSISTANT_PASSWORD")

    # 如果环境变量中没有，尝试从配置文件读取
    if not correct_password:
        config_paths = ['config.json', 'config/config.json', '../config/config.json']
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        correct_password = config.get('AI_ASSISTANT_PASSWORD')
                        if correct_password:
                            break
                except Exception:
                    pass

    # 如果还是没有找到，使用默认密码
    correct_password = correct_password or default_password

    # 直接比较密码
    return password == correct_password

def save_chat_history(user_id, chat_history):
    """
    保存聊天历史记录

    参数:
        user_id (str): 用户ID
        chat_history (list): 聊天历史记录
    """
    try:
        # 创建存储目录（如果不存在）
        os.makedirs('data/chat_history', exist_ok=True)

        # 保存聊天历史到JSON文件
        file_path = f'data/chat_history/{user_id}.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"保存聊天历史失败: {str(e)}")
        return False

def load_chat_history(user_id):
    """
    加载聊天历史记录

    参数:
        user_id (str): 用户ID

    返回:
        list: 聊天历史记录
    """
    try:
        file_path = f'data/chat_history/{user_id}.json'
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"加载聊天历史失败: {str(e)}")
        return []

