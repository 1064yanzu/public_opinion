"""AI Assistant service for generating reports and chatting"""
from typing import Generator, Dict, Optional, List
import os
import json
from openai import OpenAI
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract AI provider for extensibility"""
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict], stream: bool = False, **kwargs) -> any:
        """Chat completion"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class SiliconFlowProvider(AIProvider):
    """SiliconFlow AI provider"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY")
        self.base_url = base_url or os.environ.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def chat_completion(self, messages: List[Dict], stream: bool = False, **kwargs):
        if not self.client:
            raise ValueError("SiliconFlow API key not configured")
        
        model = kwargs.get('model', 'Qwen/Qwen2.5-7B-Instruct')
        
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **{k: v for k, v in kwargs.items() if k != 'model'}
        )


class ZhipuAIProvider(AIProvider):
    """ZhipuAI provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ZHIPU_API_KEY")
        
        if self.api_key:
            try:
                from zhipuai import ZhipuAI
                self.client = ZhipuAI(api_key=self.api_key)
            except ImportError:
                print("zhipuai package not installed")
                self.client = None
        else:
            self.client = None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def chat_completion(self, messages: List[Dict], stream: bool = False, **kwargs):
        if not self.client:
            raise ValueError("ZhipuAI API key not configured")
        
        model = kwargs.get('model', 'glm-4-flash')
        
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **{k: v for k, v in kwargs.items() if k != 'model'}
        )


class AIService:
    """High-level AI service with multiple provider support"""
    
    def __init__(self):
        self.providers = {
            'siliconflow': SiliconFlowProvider(),
            'zhipuai': ZhipuAIProvider(),
        }
        self.default_provider = self._get_default_provider()
    
    def _get_default_provider(self) -> str:
        """Get first available provider"""
        for name, provider in self.providers.items():
            if provider.is_available():
                return name
        return 'siliconflow'  # fallback
    
    def get_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        """Get AI provider instance"""
        name = provider_name or self.default_provider
        provider = self.providers.get(name)
        
        if not provider or not provider.is_available():
            raise ValueError(f"Provider {name} not available or not configured")
        
        return provider
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ):
        """
        Chat with AI
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            provider: Provider name (siliconflow, zhipuai, etc.)
            stream: Whether to stream response
            **kwargs: Additional parameters for the provider
            
        Returns:
            Response from AI (generator if stream=True)
        """
        ai_provider = self.get_provider(provider)
        return ai_provider.chat_completion(messages, stream=stream, **kwargs)
    
    def generate_report(
        self,
        analysis_context: Dict,
        sections: Optional[List[str]] = None,
        provider: Optional[str] = None
    ) -> Generator[Dict, None, None]:
        """
        Generate analysis report
        
        Args:
            analysis_context: Analysis data context
            sections: Sections to generate
            provider: AI provider to use
            
        Yields:
            Report sections as they're generated
        """
        if sections is None:
            sections = ['overview', 'analysis', 'risk', 'strategy']
        
        section_titles = {
            'overview': '## 📊 舆情概述\n\n',
            'analysis': '\n\n## 🔍 详细分析\n\n',
            'risk': '\n\n## ⚠️ 风险评估\n\n',
            'strategy': '\n\n## 💡 应对建议\n\n',
        }
        
        for section_name in sections:
            title = section_titles.get(section_name, f'\n\n## {section_name}\n\n')
            yield {'type': 'title', 'content': title}
            
            prompt = self._build_section_prompt(section_name, analysis_context)
            messages = [
                {"role": "system", "content": "你是一个专业的舆情分析师，擅长分析社交媒体数据并生成专业报告。"},
                {"role": "user", "content": prompt}
            ]
            
            try:
                response = self.chat(messages, provider=provider, stream=True)
                
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content'):
                        content = chunk.choices[0].delta.content
                        if content:
                            yield {'type': 'content', 'content': content}
            except Exception as e:
                yield {'type': 'error', 'content': f'生成{section_name}时出错: {str(e)}'}
    
    def _build_section_prompt(self, section: str, context: Dict) -> str:
        """Build prompt for specific section"""
        total_records = context.get('total_records', 0)
        sentiment = context.get('sentiment', {})
        keywords = context.get('keywords', [])
        
        base_context = f"""
数据概况：
- 总记录数：{total_records}
- 正面情绪：{sentiment.get('positive', 0)}条 ({sentiment.get('positive_pct', 0):.1f}%)
- 中性情绪：{sentiment.get('neutral', 0)}条 ({sentiment.get('neutral_pct', 0):.1f}%)
- 负面情绪：{sentiment.get('negative', 0)}条 ({sentiment.get('negative_pct', 0):.1f}%)
- 关键词：{', '.join(keywords[:10]) if keywords else '暂无'}
"""
        
        prompts = {
            'overview': f"{base_context}\n\n请基于以上数据生成舆情概述，包括整体趋势和主要特点。",
            'analysis': f"{base_context}\n\n请进行详细的情感分析和内容分析。",
            'risk': f"{base_context}\n\n请评估可能的舆情风险和负面影响。",
            'strategy': f"{base_context}\n\n请提供具体的应对策略和改进建议。",
        }
        
        return prompts.get(section, base_context)
    
    def available_providers(self) -> List[str]:
        """List available AI providers"""
        return [name for name, provider in self.providers.items() if provider.is_available()]
    
    def register_provider(self, name: str, provider: AIProvider):
        """Register a new AI provider (for extensibility)"""
        self.providers[name] = provider
