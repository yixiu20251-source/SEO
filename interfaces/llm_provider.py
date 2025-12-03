"""
LLM 提供者接口
支持本地和云端模型的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMProvider(ABC):
    """LLM 提供者抽象基类"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_role: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        生成文本内容
        
        Args:
            prompt: 用户提示词
            system_role: 系统角色提示
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            生成的文本内容
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            True 如果服务可用，否则 False
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """返回提供者名称"""
        pass

