"""
AI模型接口抽象类和具体实现
支持多种AI模型的统一接口
"""
import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional


class AIModelInterface(ABC):
    """AI模型接口抽象类"""
    
    def __init__(self, api_key: str, base_url: str = None, model_id: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model_id = model_id
    
    @abstractmethod
    def generate_stream(self, messages: list, **kwargs) -> Iterator[str]:
        """流式生成文本"""
        pass
    
    @abstractmethod
    def generate(self, messages: list, **kwargs) -> str:
        """一次性生成文本"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查模型是否可用"""
        pass


class ZhipuAIModel(AIModelInterface):
    """智谱AI模型实现"""
    
    def __init__(self, api_key: str, base_url: str = None, model_id: str = "glm-4"):
        super().__init__(api_key, base_url, model_id)
        try:
            from zhipuai import ZhipuAI
            self.client = ZhipuAI(api_key=api_key)
            self._available = True
        except Exception as e:
            print(f"智谱AI初始化失败: {str(e)}")
            self.client = None
            self._available = False
    
    def generate_stream(self, messages: list, **kwargs) -> Iterator[str]:
        """流式生成"""
        if not self.client:
            yield "模型不可用"
            return
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"生成失败: {str(e)}"
    
    def generate(self, messages: list, **kwargs) -> str:
        """一次性生成"""
        if not self.client:
            return "模型不可用"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=False,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成失败: {str(e)}"
    
    def is_available(self) -> bool:
        return self._available


class OpenAIModel(AIModelInterface):
    """OpenAI模型实现"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model_id: str = "gpt-3.5-turbo"):
        super().__init__(api_key, base_url, model_id)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._available = self._test_connection()
    
    def _test_connection(self) -> bool:
        """测试连接"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def generate_stream(self, messages: list, **kwargs) -> Iterator[str]:
        """流式生成"""
        try:
            data = {
                "model": self.model_id,
                "messages": messages,
                "stream": True,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield f"生成失败: {str(e)}"
    
    def generate(self, messages: list, **kwargs) -> str:
        """一次性生成"""
        try:
            data = {
                "model": self.model_id,
                "messages": messages,
                "stream": False,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            return f"生成失败: {str(e)}"
    
    def is_available(self) -> bool:
        return self._available


class CustomAPIModel(AIModelInterface):
    """自定义API模型实现"""
    
    def __init__(self, api_key: str, base_url: str, model_id: str):
        super().__init__(api_key, base_url, model_id)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._available = True
    
    def generate_stream(self, messages: list, **kwargs) -> Iterator[str]:
        """流式生成 - 适配自定义API"""
        try:
            data = {
                "model": self.model_id,
                "messages": messages,
                "stream": True,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield f"生成失败: {str(e)}"
    
    def generate(self, messages: list, **kwargs) -> str:
        """一次性生成"""
        try:
            data = {
                "model": self.model_id,
                "messages": messages,
                "stream": False,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            return f"生成失败: {str(e)}"
    
    def is_available(self) -> bool:
        return self._available


def create_ai_model() -> Optional[AIModelInterface]:
    """根据环境变量创建AI模型实例"""

    # 从环境变量读取配置
    model_type = os.getenv('AI_MODEL_TYPE', 'zhipuai').lower()
    api_key = os.getenv('AI_API_KEY', '')
    base_url = os.getenv('AI_BASE_URL', '')
    model_id = os.getenv('AI_MODEL_ID', '')

    if not api_key:
        # 不输出警告，让调用方处理
        return None
    
    try:
        if model_type == 'zhipuai':
            model_id = model_id or 'glm-4'
            return ZhipuAIModel(api_key, base_url, model_id)
        
        elif model_type == 'openai':
            base_url = base_url or 'https://api.openai.com/v1'
            model_id = model_id or 'gpt-3.5-turbo'
            return OpenAIModel(api_key, base_url, model_id)
        
        elif model_type == 'custom':
            if not base_url or not model_id:
                print("错误: 自定义模型需要设置AI_BASE_URL和AI_MODEL_ID")
                return None
            return CustomAPIModel(api_key, base_url, model_id)
        
        else:
            print(f"错误: 不支持的模型类型 {model_type}")
            return None
            
    except Exception as e:
        print(f"创建AI模型失败: {str(e)}")
        return None
