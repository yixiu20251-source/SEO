"""
域名分发器接口
处理多域名/子域名的路由和文件组织
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class DomainDispatcher(ABC):
    """域名分发器抽象基类"""
    
    @abstractmethod
    def resolve_path(
        self,
        project_config: Dict[str, Any],
        hostname: str,
        path: str = "/"
    ) -> str:
        """
        解析文件输出路径
        
        Args:
            project_config: 项目配置
            hostname: 主机名（如 example.com 或 blog.example.com）
            path: URL 路径
            
        Returns:
            输出文件的相对路径（相对于 /dist）
        """
        pass
    
    @abstractmethod
    def get_topology_config(self, project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取域名拓扑配置
        
        Args:
            project_config: 项目配置
            
        Returns:
            拓扑配置列表，每个元素包含 hostname, role, strategy 等
        """
        pass
    
    @abstractmethod
    def should_link_domains(
        self,
        source_hostname: str,
        target_hostname: str,
        project_config: Dict[str, Any]
    ) -> bool:
        """
        判断两个域名是否应该相互链接
        
        Args:
            source_hostname: 源主机名
            target_hostname: 目标主机名
            project_config: 项目配置
            
        Returns:
            True 如果应该链接，否则 False
        """
        pass

