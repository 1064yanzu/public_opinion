"""AI模型接口抽象类和具体实现
支持多种AI模型的统一接口
"""
import os
import json
import requests
import time
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional, Union


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
    
    def chat(self, messages: list, stream: bool = False, **kwargs) -> Union[Iterator[str], str]:
        """统一聊天接口，支持流式和非流式"""
        try:
            if stream:
                # 优先尝试流式
                try:
                    return self.generate_stream(messages, **kwargs)
                except Exception as e:
                    print(f"流式模式失败，降级到非流式: {str(e)}")
                    # 降级到非流式
                    result = self.generate(messages, **kwargs)
                    yield result
                    return
            else:
                return self.generate(messages, **kwargs)
        except Exception as e:
            error_msg = f"AI模型调用失败: {str(e)}"
            if stream:
                yield error_msg
            else:
                return error_msg


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
        self.timeout = 30
        self.max_retries = 3
        self._available = self._test_connection()
    
    def _test_connection(self) -> bool:
        """测试连接"""
        try:
            print(f"[OpenAI] 连接测试 - URL: {self.base_url}/models, Model: {self.model_id}")
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 200:
                print(f"[OpenAI] 连接测试成功")
                return True
            else:
                print(f"[OpenAI] 连接测试失败 - 状态码: {response.status_code}, 响应: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"[OpenAI] 连接测试异常: {str(e)}")
            return False
    
    def generate_stream(self, messages: list, **kwargs) -> Iterator[str]:
        """流式生成"""
        for attempt in range(self.max_retries):
            try:
                data = {
                    "model": self.model_id,
                    "messages": messages,
                    "stream": True,
                    **kwargs
                }
                
                print(f"[OpenAI] 流式请求 - URL: {self.base_url}/chat/completions, Model: {self.model_id}")
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    stream=True,
                    timeout=self.timeout
                )
                
                # 检查HTTP状态码
                if response.status_code == 401:
                    error_msg = f"认证失败(401): API密钥无效或已过期"
                    print(f"[OpenAI] {error_msg}")
                    raise Exception(error_msg)
                elif response.status_code == 403:
                    error_msg = f"权限不足(403): 无权访问此模型或API"
                    print(f"[OpenAI] {error_msg}")
                    raise Exception(error_msg)
                elif response.status_code == 404:
                    error_msg = f"模型不存在(404): {self.model_id}"
                    print(f"[OpenAI] {error_msg}")
                    raise Exception(error_msg)
                elif response.status_code == 429:
                    error_msg = f"请求过于频繁(429): 已达到API配额限制"
                    print(f"[OpenAI] {error_msg}")
                    raise Exception(error_msg)
                elif response.status_code >= 500:
                    error_msg = f"服务器错误({response.status_code}): 请稍后重试"
                    print(f"[OpenAI] {error_msg}, 响应: {response.text[:200]}")
                    raise Exception(error_msg)
                elif response.status_code != 200:
                    error_text = response.text[:200] if response.text else ''
                    error_msg = f"API请求失败({response.status_code}): {error_text}"
                    print(f"[OpenAI] {error_msg}")
                    raise Exception(error_msg)
                
                print(f"[OpenAI] 流式请求成功，开始接收数据")
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(data_str)
                                if 'choices' in chunk_data and chunk_data['choices']:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
                return
                
            except requests.exceptions.ConnectionError as e:
                error_msg = f"网络连接失败: {str(e)}"
                print(f"[OpenAI] {error_msg}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                yield error_msg
                return
            except requests.exceptions.Timeout as e:
                error_msg = f"请求超时: {str(e)}"
                print(f"[OpenAI] {error_msg}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                yield error_msg
                return
            except Exception as e:
                error_msg = f"流式生成失败: {str(e)}"
                print(f"[OpenAI] {error_msg}")
                yield error_msg
                return
    
    def generate(self, messages: list, **kwargs) -> str:
        """一次性生成"""
        for attempt in range(self.max_retries):
            try:
                data = {
                    "model": self.model_id,
                    "messages": messages,
                    "stream": False,
                    **kwargs
                }
                
                print(f"[OpenAI] 非流式请求 - URL: {self.base_url}/chat/completions, Model: {self.model_id}")
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=self.timeout
                )
                
                # 检查HTTP状态码
                if response.status_code == 401:
                    error_msg = f"认证失败(401): API密钥无效或已过期"
                    print(f"[OpenAI] {error_msg}")
                    return error_msg
                elif response.status_code == 403:
                    error_msg = f"权限不足(403): 无权访问此模型或API"
                    print(f"[OpenAI] {error_msg}")
                    return error_msg
                elif response.status_code == 404:
                    error_msg = f"模型不存在(404): {self.model_id}"
                    print(f"[OpenAI] {error_msg}")
                    return error_msg
                elif response.status_code == 429:
                    error_msg = f"请求过于频繁(429): 已达到API配额限制"
                    print(f"[OpenAI] {error_msg}")
                    return error_msg
                elif response.status_code >= 500:
                    error_msg = f"服务器错误({response.status_code}): 请稍后重试"
                    print(f"[OpenAI] {error_msg}, 响应: {response.text[:200]}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return error_msg
                elif response.status_code != 200:
                    error_text = response.text[:200] if response.text else ''
                    error_msg = f"API请求失败({response.status_code}): {error_text}"
                    print(f"[OpenAI] {error_msg}")
                    return error_msg
                
                result = response.json()
                print(f"[OpenAI] 非流式请求成功，获得响应")
                return result['choices'][0]['message']['content']
                
            except requests.exceptions.ConnectionError as e:
                error_msg = f"网络连接失败: {str(e)}"
                print(f"[OpenAI] {error_msg}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return error_msg
            except requests.exceptions.Timeout as e:
                error_msg = f"请求超时: {str(e)}"
                print(f"[OpenAI] {error_msg}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return error_msg
            except Exception as e:
                error_msg = f"非流式生成失败: {str(e)}"
                print(f"[OpenAI] {error_msg}")
                return error_msg
    
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

    # 小工具：环境变量清洗函数
    def _clean(s: Optional[str]) -> str:
        if s is None:
            return ''
        # 去除首尾空白并清理包裹的引号/反引号
        s = s.strip().strip('"').strip("'").strip('`').strip()
        # 把连续空白压缩为单个空格
        s = ' '.join(s.split())
        return s

    # 从环境变量读取配置
    model_type = _clean(os.getenv('AI_MODEL_TYPE', 'zhipuai')).lower()
    api_key = _clean(os.getenv('AI_API_KEY', ''))
    base_url = _clean(os.getenv('AI_BASE_URL', ''))
    model_id = _clean(os.getenv('AI_MODEL_ID', ''))

    # 兼容：如果未提供通用变量，尝试使用 SiliconFlow_* 作为回落
    if not api_key:
        api_key = _clean(os.getenv('SILICONFLOW_API_KEY', '')) or api_key
    if not base_url:
        base_url = _clean(os.getenv('SILICONFLOW_BASE_URL', '')) or base_url
    if not model_id:
        model_id = _clean(os.getenv('SILICONFLOW_MODEL_ID', '')) or model_id

    # 配置摘要（掩码显示密钥）
    masked_key = api_key[:8] + '***' + api_key[-4:] if len(api_key) > 12 else 'sk-***'
    print(f"[AI配置] 类型: {model_type}, URL: {base_url}, 模型: {model_id}, 密钥: {masked_key}")

    if not api_key:
        print("[AI配置] 错误: 未提供API密钥")
        return None
    
    try:
        if model_type == 'zhipuai':
            model_id = model_id or 'glm-4'
            print(f"[AI配置] 创建智谱AI模型: {model_id}")
            return ZhipuAIModel(api_key, base_url, model_id)
        
        elif model_type == 'openai':
            # OpenAI兼容模式需要base_url和model_id
            if not base_url or not model_id:
                print("[AI配置] 错误: OpenAI兼容模式需要设置AI_BASE_URL和AI_MODEL_ID")
                print("[AI配置] 示例: AI_BASE_URL=https://api.xxx.com AI_MODEL_ID=gpt-3.5-turbo-0125")
                return None
            
            # 规范化 base_url：移除末尾斜杠并确保以 /v1 结尾
            base_url = base_url.rstrip('/')
            if not base_url.endswith('/v1'):
                base_url = base_url + '/v1'
                print(f"[AI配置] 自动补全 /v1 后缀: {base_url}")
            
            print(f"[AI配置] 创建OpenAI兼容模型: {model_id} @ {base_url}")
            return OpenAIModel(api_key, base_url, model_id)
        
        elif model_type == 'custom':
            if not base_url or not model_id:
                print("[AI配置] 错误: 自定义模型需要设置AI_BASE_URL和AI_MODEL_ID")
                return None
            print(f"[AI配置] 创建自定义API模型: {model_id} @ {base_url}")
            return CustomAPIModel(api_key, base_url, model_id)
        
        else:
            print(f"[AI配置] 错误: 不支持的模型类型 {model_type}")
            print("[AI配置] 支持的类型: zhipuai, openai, custom")
            return None
            
    except Exception as e:
        print(f"[AI配置] 创建AI模型失败: {str(e)}")
        return None
