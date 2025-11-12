"""
设置AI助手所需的环境变量
"""
import os
import sys

def set_env_vars():
    """设置环境变量"""
    # 检查是否提供了API密钥
    if len(sys.argv) < 2:
        print("使用方法: python set_env.py <API_KEY> [PASSWORD]")
        print("例如: python set_env.py sk-xxxxxxxxxxxxxxxx yuqing2024")
        return
    
    # 获取命令行参数
    api_key = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else "yuqing2024"
    
    # 设置环境变量
    os.environ["SILICONFLOW_API_KEY"] = api_key
    os.environ["AI_ASSISTANT_PASSWORD"] = password
    
    # 打印设置的环境变量
    print(f"已设置环境变量:")
    print(f"SILICONFLOW_API_KEY={api_key}")
    print(f"AI_ASSISTANT_PASSWORD={password}")
    
    # 可以选择将环境变量写入.env文件
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"# AI助手环境变量\n")
        f.write(f"SILICONFLOW_API_KEY={api_key}\n")
        f.write(f"AI_ASSISTANT_PASSWORD={password}\n")
    
    print(f"环境变量已保存到.env文件")

if __name__ == "__main__":
    set_env_vars()
