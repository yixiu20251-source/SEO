"""
模板渲染器接口
定义 HTML 模板渲染方法
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class TemplateRenderer(ABC):
    """模板渲染器抽象基类"""
    
    @abstractmethod
    def render(
        self,
        template_name: str,
        context: Dict[str, Any],
        theme: str = "default"
    ) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板文件名
            context: 模板上下文数据
            theme: 主题名称
            
        Returns:
            渲染后的 HTML 字符串
        """
        pass
    
    @abstractmethod
    def register_template(self, name: str, template_path: str) -> None:
        """
        注册模板
        
        Args:
            name: 模板名称
            template_path: 模板文件路径
        """
        pass
    
    @abstractmethod
    def inject_seo_data(self, html: str, seo_data: Dict[str, Any]) -> str:
        """
        注入 SEO 数据（JSON-LD）
        
        Args:
            html: HTML 内容
            seo_data: SEO 结构化数据
            
        Returns:
            注入后的 HTML
        """
        pass

