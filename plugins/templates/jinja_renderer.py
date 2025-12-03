"""
Jinja2 模板渲染器
实现 TemplateRenderer 接口
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from interfaces.template_renderer import TemplateRenderer
from core.logger import Logger


class JinjaRenderer(TemplateRenderer):
    """Jinja2 模板渲染器"""
    
    def __init__(self, template_dir: str = "templates"):
        """
        初始化 Jinja2 渲染器
        
        Args:
            template_dir: 模板目录路径
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.logger = Logger()
        
        # 初始化 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 注册自定义过滤器
        self._register_filters()
    
    def _register_filters(self):
        """注册自定义 Jinja2 过滤器"""
        
        @self.env.filter('to_json')
        def to_json_filter(value):
            """将值转换为 JSON 字符串"""
            return json.dumps(value, ensure_ascii=False)
        
        @self.env.filter('format_date')
        def format_date_filter(value, format_str='%Y-%m-%d'):
            """格式化日期"""
            if hasattr(value, 'strftime'):
                return value.strftime(format_str)
            return str(value)
    
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
        try:
            # 添加主题到上下文
            context['theme'] = theme
            
            # 加载模板
            template = self.env.get_template(template_name)
            
            # 渲染
            html = template.render(**context)
            
            self.logger.debug(f"渲染模板: {template_name} (主题: {theme})")
            return html
            
        except Exception as e:
            self.logger.error(f"渲染模板失败: {template_name}, 错误: {e}")
            raise
    
    def register_template(self, name: str, template_path: str) -> None:
        """
        注册模板（Jinja2 使用文件系统加载器，此方法用于验证模板存在）
        
        Args:
            name: 模板名称
            template_path: 模板文件路径
        """
        path = Path(template_path)
        if not path.exists():
            self.logger.warning(f"模板文件不存在: {template_path}")
        else:
            self.logger.debug(f"注册模板: {name} -> {template_path}")
    
    def inject_seo_data(self, html: str, seo_data: Dict[str, Any]) -> str:
        """
        注入 SEO 数据（JSON-LD）
        
        Args:
            html: HTML 内容
            seo_data: SEO 结构化数据
            
        Returns:
            注入后的 HTML
        """
        try:
            # 生成 JSON-LD 脚本
            json_ld_scripts = []
            
            # Article 结构化数据
            if 'article' in seo_data:
                article_script = self._generate_json_ld('Article', seo_data['article'])
                json_ld_scripts.append(article_script)
            
            # HowTo 结构化数据
            if 'howto' in seo_data:
                howto_script = self._generate_json_ld('HowTo', seo_data['howto'])
                json_ld_scripts.append(howto_script)
            
            # BreadcrumbList 结构化数据
            if 'breadcrumbs' in seo_data:
                breadcrumb_script = self._generate_json_ld('BreadcrumbList', seo_data['breadcrumbs'])
                json_ld_scripts.append(breadcrumb_script)
            
            # 注入到 </head> 之前
            if json_ld_scripts:
                scripts_html = '\n'.join(json_ld_scripts)
                html = html.replace('</head>', f'{scripts_html}\n</head>')
                self.logger.debug(f"注入 {len(json_ld_scripts)} 个 JSON-LD 脚本")
            
            return html
            
        except Exception as e:
            self.logger.error(f"注入 SEO 数据失败: {e}")
            return html
    
    def _generate_json_ld(self, schema_type: str, data: Dict[str, Any]) -> str:
        """
        生成 JSON-LD 脚本标签
        
        Args:
            schema_type: Schema.org 类型
            data: 结构化数据
            
        Returns:
            JSON-LD 脚本 HTML
        """
        json_data = {
            "@context": "https://schema.org",
            "@type": schema_type,
            **data
        }
        
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        return f'<script type="application/ld+json">\n{json_str}\n</script>'

