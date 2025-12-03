"""
链接网络（Link Mesh）
实现上下文内部链接
"""

from typing import Dict, Any, List, Set
from core.logger import Logger


class LinkMesh:
    """链接网络管理器"""
    
    def __init__(self):
        self.logger = Logger()
        self.link_graph: Dict[str, Set[str]] = {}  # 页面URL -> 链接到的URL集合
        self.page_contexts: Dict[str, str] = {}  # 页面URL -> MaskContext
    
    def add_page(self, url: str, mask_context: str):
        """
        添加页面到链接网络
        
        Args:
            url: 页面URL
            mask_context: 页面的伪装上下文
        """
        if url not in self.link_graph:
            self.link_graph[url] = set()
        self.page_contexts[url] = mask_context
        self.logger.debug(f"添加页面到链接网络: {url} ({mask_context})")
    
    def should_link(self, source_url: str, target_url: str) -> bool:
        """
        判断两个页面是否应该相互链接
        
        规则：只有相同 MaskContext 的页面才能相互链接
        
        Args:
            source_url: 源页面URL
            target_url: 目标页面URL
            
        Returns:
            True 如果应该链接，否则 False
        """
        source_context = self.page_contexts.get(source_url)
        target_context = self.page_contexts.get(target_url)
        
        if not source_context or not target_context:
            return False
        
        # 只有相同上下文才能链接
        should = source_context == target_context
        if should:
            self.logger.debug(f"允许链接: {source_url} -> {target_url} (上下文: {source_context})")
        else:
            self.logger.debug(f"拒绝链接: {source_url} -> {target_url} (上下文不匹配: {source_context} != {target_context})")
        
        return should
    
    def add_link(self, source_url: str, target_url: str):
        """
        添加链接
        
        Args:
            source_url: 源页面URL
            target_url: 目标页面URL
        """
        if self.should_link(source_url, target_url):
            if source_url not in self.link_graph:
                self.link_graph[source_url] = set()
            self.link_graph[source_url].add(target_url)
            self.logger.debug(f"添加链接: {source_url} -> {target_url}")
        else:
            self.logger.warning(f"拒绝添加链接（上下文不匹配）: {source_url} -> {target_url}")
    
    def get_links(self, url: str) -> List[str]:
        """
        获取页面的所有链接
        
        Args:
            url: 页面URL
            
        Returns:
            链接URL列表
        """
        return list(self.link_graph.get(url, set()))
    
    def generate_contextual_links(
        self,
        current_url: str,
        all_pages: List[Dict[str, Any]],
        max_links: int = 5
    ) -> List[Dict[str, Any]]:
        """
        为当前页面生成上下文相关的内部链接
        
        Args:
            current_url: 当前页面URL
            all_pages: 所有页面列表（包含 url, title, mask_context 等）
            max_links: 最大链接数
            
        Returns:
            链接列表，每个元素包含 url, title 等
        """
        current_context = self.page_contexts.get(current_url)
        if not current_context:
            return []
        
        # 筛选相同上下文的页面
        candidate_pages = [
            page for page in all_pages
            if page.get("url") != current_url
            and page.get("mask_context") == current_context
        ]
        
        # 限制链接数量
        linked_pages = candidate_pages[:max_links]
        
        self.logger.debug(f"为 {current_url} 生成 {len(linked_pages)} 个上下文链接")
        return linked_pages

