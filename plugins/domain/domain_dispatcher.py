"""
Hydra 域名分发器
处理多域名/子域名的路由和文件组织
支持 Swarm Mode 和 Composite Mode
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from interfaces.domain_dispatcher import DomainDispatcher
from core.logger import Logger


class HydraDomainDispatcher(DomainDispatcher):
    """Hydra 域名分发器实现"""
    
    def __init__(self):
        self.logger = Logger()
        self.topology_cache: Optional[List[Dict[str, Any]]] = None
    
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
            
        Raises:
            ValueError: 如果检测到路径遍历攻击
        """
        output_config = project_config.get("output", {})
        base_path = output_config.get("path", "dist")
        
        # 清理路径
        path = path.strip("/")
        if not path:
            path = "index.html"
        elif not path.endswith(".html") and "." not in Path(path).name:
            # 如果是目录路径，添加 index.html
            path = f"{path}/index.html" if path else "index.html"
        
        # 根据模式决定输出路径
        mode = project_config.get("mode", "composite")
        
        if mode == "swarm":
            # Swarm Mode: keyword.domain.com -> dist/keyword.domain.com/
            output_path = f"{base_path}/{hostname}/{path}"
        else:
            # Composite Mode: 根据拓扑配置组织
            topology = self.get_topology_config(project_config)
            hostname_base = self._extract_base_domain(hostname)
            
            # 查找匹配的拓扑配置
            matched_config = None
            for topo in topology:
                topo_hostname = topo.get("hostname", "")
                if hostname == topo_hostname or hostname.endswith(f".{topo_hostname}"):
                    matched_config = topo
                    break
            
            if matched_config:
                # 使用配置中的 hostname 作为目录名
                output_path = f"{base_path}/{matched_config['hostname']}/{path}"
            else:
                # 默认使用完整 hostname
                output_path = f"{base_path}/{hostname}/{path}"
        
        # 安全验证：防止路径遍历攻击
        base_path_obj = Path(base_path).resolve()
        safe_path_obj = Path(output_path).resolve()
        
        try:
            # 检查解析后的路径是否在base_path内
            safe_path_obj.relative_to(base_path_obj)
        except ValueError:
            # 路径不在base_path内，检测到路径遍历攻击
            self.logger.error(f"Security Violation: Path Traversal detected - {output_path}")
            raise ValueError(f"Security Violation: Path Traversal detected - attempted path: {output_path}")
        
        self.logger.debug(f"解析路径: {hostname}{path} -> {output_path}")
        return output_path
    
    def get_topology_config(self, project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取域名拓扑配置
        
        Args:
            project_config: 项目配置
            
        Returns:
            拓扑配置列表，每个元素包含 hostname, role, strategy 等
        """
        if self.topology_cache is not None:
            return self.topology_cache
        
        topology = project_config.get("topology", [])
        
        # 如果没有显式配置，创建默认拓扑
        if not topology:
            base_domain = project_config.get("base_domain", "example.com")
            topology = [
                {
                    "hostname": base_domain,
                    "role": "LandingPage",
                    "strategy": "Business Strategy",
                    "mask_context": project_config.get("default_mask_context", "Technology")
                }
            ]
        
        self.topology_cache = topology
        self.logger.info(f"加载拓扑配置: {len(topology)} 个域名")
        return topology
    
    def should_link_domains(
        self,
        source_hostname: str,
        target_hostname: str,
        project_config: Dict[str, Any]
    ) -> bool:
        """
        判断两个域名是否应该相互链接
        
        规则：只有相同 MaskContext 的域名才能相互链接
        
        Args:
            source_hostname: 源主机名
            target_hostname: 目标主机名
            project_config: 项目配置
            
        Returns:
            True 如果应该链接，否则 False
        """
        topology = self.get_topology_config(project_config)
        
        # 查找源和目标域名的配置
        source_config = self._find_topology_config(source_hostname, topology)
        target_config = self._find_topology_config(target_hostname, topology)
        
        if not source_config or not target_config:
            return False
        
        source_context = source_config.get("mask_context")
        target_context = target_config.get("mask_context")
        
        should_link = source_context == target_context
        
        if should_link:
            self.logger.debug(f"允许链接: {source_hostname} -> {target_hostname} (上下文: {source_context})")
        else:
            self.logger.debug(f"拒绝链接: {source_hostname} -> {target_hostname} (上下文不匹配)")
        
        return should_link
    
    def _find_topology_config(
        self,
        hostname: str,
        topology: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        查找匹配的拓扑配置
        
        Args:
            hostname: 主机名
            topology: 拓扑配置列表
            
        Returns:
            匹配的配置字典，如果未找到则返回 None
        """
        for config in topology:
            config_hostname = config.get("hostname", "")
            if hostname == config_hostname:
                return config
            # 支持子域名匹配
            if hostname.endswith(f".{config_hostname}"):
                return config
        
        return None
    
    def _extract_base_domain(self, hostname: str) -> str:
        """
        提取基础域名
        
        Args:
            hostname: 完整主机名
            
        Returns:
            基础域名
        """
        parts = hostname.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return hostname
    
    def generate_wildcard_mapping(
        self,
        keywords: List[str],
        base_domain: str
    ) -> List[Dict[str, Any]]:
        """
        生成通配符映射（Swarm Mode）
        
        Args:
            keywords: 关键词列表
            base_domain: 基础域名
            
        Returns:
            拓扑配置列表
        """
        mapping = []
        for keyword in keywords:
            # 清理关键词，移除特殊字符
            clean_keyword = re.sub(r'[^\w-]', '', keyword.lower().replace(' ', '-'))
            hostname = f"{clean_keyword}.{base_domain}"
            
            mapping.append({
                "hostname": hostname,
                "role": "ContentPage",
                "strategy": "SEO Strategy",
                "keyword": keyword,
                "mask_context": "Technology"  # 默认上下文，可从配置读取
            })
        
        self.logger.info(f"生成通配符映射: {len(mapping)} 个域名")
        return mapping
    
    def build_shared_navbar(
        self,
        current_hostname: str,
        project_config: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        构建共享导航栏（Composite Mode）
        
        Args:
            current_hostname: 当前主机名
            project_config: 项目配置
            
        Returns:
            导航项列表
        """
        topology = self.get_topology_config(project_config)
        navbar = []
        
        for config in topology:
            hostname = config.get("hostname", "")
            role = config.get("role", "Page")
            
            # 生成友好的标签
            label = role.replace("Page", "").strip()
            if not label:
                # 从 hostname 提取
                label = hostname.split(".")[0].capitalize()
            
            navbar.append({
                "label": label,
                "url": f"https://{hostname}/",
                "hostname": hostname
            })
        
        return navbar

