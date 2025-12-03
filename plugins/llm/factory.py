"""
LLM 工厂
根据配置创建相应的 LLM 提供者实例
"""

from typing import Dict, Any, Optional
from interfaces.llm_provider import LLMProvider
from plugins.llm.ollama_provider import OllamaProvider
from plugins.llm.openai_provider import OpenAIProvider
from core.logger import Logger


class LLMFactory:
    """LLM 提供者工厂"""
    
    _providers: Dict[str, LLMProvider] = {}
    logger = Logger()
    
    @staticmethod
    def get_provider(config: Dict[str, Any]) -> LLMProvider:
        """
        根据配置获取 LLM 提供者实例
        
        Args:
            config: LLM 配置字典，包含 provider, model 等字段
            
        Returns:
            LLMProvider 实例
        """
        provider_type = config.get("provider", "ollama").lower()
        model = config.get("model", "llama3")
        
        # 生成缓存键
        cache_key = f"{provider_type}:{model}"
        
        # 如果已存在实例，直接返回
        if cache_key in LLMFactory._providers:
            LLMFactory.logger.debug(f"使用缓存的 LLM 提供者: {cache_key}")
            return LLMFactory._providers[cache_key]
        
        # 创建新实例
        if provider_type == "ollama":
            base_url = config.get("base_url", "http://localhost:11434")
            provider = OllamaProvider(base_url=base_url, model=model)
            LLMFactory.logger.info(f"创建 Ollama 提供者: {model}")
            
        elif provider_type == "openai":
            api_key = config.get("api_key")
            base_url = config.get("base_url", "https://api.openai.com/v1")
            provider = OpenAIProvider(api_key=api_key, base_url=base_url, model=model)
            LLMFactory.logger.info(f"创建 OpenAI 提供者: {model}")
            
        else:
            raise ValueError(f"不支持的 LLM 提供者类型: {provider_type}")
        
        # 缓存实例
        LLMFactory._providers[cache_key] = provider
        return provider
    
    @staticmethod
    def clear_cache():
        """清空提供者缓存"""
        LLMFactory._providers.clear()
        LLMFactory.logger.debug("清空 LLM 提供者缓存")

