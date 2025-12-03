"""
流量过滤器
处理 404 错误，重定向到目标着陆页
"""

from typing import Dict, Any, Optional
from core.logger import Logger


class TrafficFilter:
    """流量过滤器"""
    
    def __init__(self, landing_page: str = "/"):
        """
        初始化流量过滤器
        
        Args:
            landing_page: 默认着陆页路径
        """
        self.landing_page = landing_page
        self.logger = Logger()
        self.redirect_rules: Dict[str, str] = {}  # 404路径 -> 重定向目标
    
    def add_redirect_rule(self, not_found_path: str, redirect_to: str):
        """
        添加重定向规则
        
        Args:
            not_found_path: 404 路径（支持正则）
            redirect_to: 重定向目标
        """
        self.redirect_rules[not_found_path] = redirect_to
        self.logger.debug(f"添加重定向规则: {not_found_path} -> {redirect_to}")
    
    def handle_404(self, request_path: str) -> Optional[str]:
        """
        处理 404 请求，返回重定向目标
        
        Args:
            request_path: 请求路径
            
        Returns:
            重定向目标路径（301），如果不需要重定向则返回 None
        """
        # 检查是否有匹配的重定向规则
        for pattern, redirect_to in self.redirect_rules.items():
            import re
            if re.match(pattern, request_path):
                self.logger.info(f"404 重定向: {request_path} -> {redirect_to} (301)")
                return redirect_to
        
        # 默认重定向到着陆页
        if request_path != self.landing_page:
            self.logger.info(f"404 默认重定向: {request_path} -> {self.landing_page} (301)")
            return self.landing_page
        
        return None
    
    def generate_nginx_404_handler(self) -> str:
        """
        生成 Nginx 404 处理配置片段
        
        Returns:
            Nginx 配置片段
        """
        # 使用字符串格式化避免 f-string 中的注释问题
        landing = self.landing_page
        config = f"""    # 404 处理 - 重定向到着陆页
    error_page 404 =301 {landing};
    
    # 自定义 404 处理（如果需要更复杂的逻辑）
    # location ~ ^/(?!api|static|assets) {{
    #     try_files $uri $uri/ =301 {landing};
    # }}
"""
        return config

