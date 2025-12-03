"""
内容策略接口
定义内容生成和规划的方法
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ContentStrategy(ABC):
    """内容策略抽象基类"""
    
    @abstractmethod
    async def plan_outline(self, keyword: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        规划内容大纲
        
        Args:
            keyword: 目标关键词
            context: 上下文信息（mask_context, persona 等）
            
        Returns:
            包含大纲结构的字典
        """
        pass
    
    @abstractmethod
    async def write_content(
        self,
        outline: Dict[str, Any],
        target_keyword: str,
        mask_context: str,
        persona: str
    ) -> str:
        """
        根据大纲生成完整内容
        
        Args:
            outline: 内容大纲
            target_keyword: 目标关键词（需要伪装）
            mask_context: 伪装上下文（如 "Industrial Machinery"）
            persona: 人物角色（如 "Senior Engineer"）
            
        Returns:
            生成的完整内容
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """返回策略名称"""
        pass

