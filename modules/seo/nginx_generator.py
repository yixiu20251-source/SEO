"""
Nginx 配置生成器
生成动态 Nginx 配置，支持通配符域名和子域名路由
"""

from typing import Dict, Any, List
from pathlib import Path
from core.logger import Logger


class NginxGenerator:
    """Nginx 配置生成器"""
    
    def __init__(self):
        self.logger = Logger()
    
    def generate_config(
        self,
        project_config: Dict[str, Any],
        topology: List[Dict[str, Any]],
        output_path: str = "nginx.conf"
    ) -> str:
        """
        生成完整的 Nginx 配置文件
        
        Args:
            project_config: 项目配置
            topology: 域名拓扑配置
            output_path: 输出文件路径
            
        Returns:
            Nginx 配置内容
        """
        base_domain = project_config.get("base_domain", "example.com")
        output_dir = project_config.get("output", {}).get("path", "dist")
        mode = project_config.get("mode", "composite")
        
        config_lines = []
        
        # HTTP 服务器块（重定向到 HTTPS）
        config_lines.append(self._generate_http_server(base_domain))
        config_lines.append("")
        
        # HTTPS 服务器块
        if mode == "swarm":
            # Swarm Mode: 使用通配符匹配
            config_lines.append(self._generate_wildcard_server(
                base_domain,
                output_dir,
                topology
            ))
        else:
            # Composite Mode: 为每个域名生成单独的服务器块
            for topo in topology:
                hostname = topo.get("hostname", "")
                if hostname:
                    config_lines.append(self._generate_single_server(
                        hostname,
                        output_dir,
                        topo
                    ))
                    config_lines.append("")
        
        config_content = "\n".join(config_lines)
        
        # 写入文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(config_content, encoding='utf-8')
        
        self.logger.info(f"Nginx 配置已生成: {output_path}")
        return config_content
    
    def _generate_http_server(self, base_domain: str) -> str:
        """
        生成 HTTP 服务器块（重定向到 HTTPS）
        
        Args:
            base_domain: 基础域名
            
        Returns:
            HTTP 服务器块配置
        """
        return f"""# HTTP 服务器 - 重定向到 HTTPS
server {{
    listen 80;
    listen [::]:80;
    server_name {base_domain} *.{base_domain};
    
    # 重定向所有 HTTP 请求到 HTTPS
    return 301 https://$host$request_uri;
}}"""
    
    def _generate_wildcard_server(
        self,
        base_domain: str,
        output_dir: str,
        topology: List[Dict[str, Any]]
    ) -> str:
        """
        生成通配符服务器块（Swarm Mode）
        
        Args:
            base_domain: 基础域名
            output_dir: 输出目录
            topology: 拓扑配置
            
        Returns:
            通配符服务器块配置
        """
        return f"""# HTTPS 服务器 - 通配符模式 (Swarm Mode)
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    # 使用正则表达式捕获子域名
    server_name ~^(?<subdomain>.+)\\.{base_domain.replace('.', '\\.')}$;
    
    # SSL 配置（需要替换为实际证书路径）
    ssl_certificate /etc/nginx/ssl/{base_domain}/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/{base_domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 根目录指向对应的子域名目录
    root /var/www/{output_dir}/$subdomain.{base_domain};
    index index.html;
    
    # 日志
    access_log /var/log/nginx/{base_domain}-access.log;
    error_log /var/log/nginx/{base_domain}-error.log;
    
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # 主要位置块
    location / {{
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \\.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
    
    # 404 处理 - 重定向到主域名
    error_page 404 =301 https://{base_domain}/;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}}"""
    
    def _generate_single_server(
        self,
        hostname: str,
        output_dir: str,
        topo_config: Dict[str, Any]
    ) -> str:
        """
        生成单个域名服务器块（Composite Mode）
        
        Args:
            hostname: 主机名
            output_dir: 输出目录
            topo_config: 拓扑配置
            
        Returns:
            单个服务器块配置
        """
        return f"""# HTTPS 服务器 - {hostname}
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {hostname};
    
    # SSL 配置（需要替换为实际证书路径）
    ssl_certificate /etc/nginx/ssl/{hostname}/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/{hostname}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 根目录
    root /var/www/{output_dir}/{hostname};
    index index.html;
    
    # 日志
    access_log /var/log/nginx/{hostname}-access.log;
    error_log /var/log/nginx/{hostname}-error.log;
    
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # 主要位置块
    location / {{
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \\.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
    
    # 404 处理
    error_page 404 =301 /;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}}"""
    
    def generate_ssl_setup_script(self, base_domain: str) -> str:
        """
        生成 SSL 证书设置脚本（使用 Let's Encrypt）
        
        Args:
            base_domain: 基础域名
            
        Returns:
            Shell 脚本内容
        """
        script = f"""#!/bin/bash
# SSL 证书设置脚本 - {base_domain}

# 安装 Certbot（如果未安装）
# sudo apt-get update
# sudo apt-get install certbot python3-certbot-nginx

# 为通配符域名申请证书（需要 DNS 验证）
# certbot certonly --manual --preferred-challenges dns -d {base_domain} -d *.{base_domain}

# 或者为单个域名申请证书
# certbot --nginx -d {base_domain}

echo "SSL 证书设置完成"
"""
        return script

