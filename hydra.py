#!/usr/bin/env python3
"""
Hydra - The Polymorphic SEO Ecosystem
主入口文件
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List

# 导入核心组件
from core.logger import Logger
from core.config_loader import ConfigLoader
from core.pipeline import Pipeline

# 导入插件
from plugins.llm.factory import LLMFactory
from plugins.templates.jinja_renderer import JinjaRenderer
from plugins.domain.domain_dispatcher import HydraDomainDispatcher

# 导入业务逻辑
from modules.mimicry.content_strategy import MimicryContentStrategy
from modules.seo.link_mesh import LinkMesh
from modules.seo.seo_data_builder import SEODataBuilder
from modules.seo.nginx_generator import NginxGenerator


class HydraEngine:
    """Hydra 主引擎"""
    
    def __init__(self, config_path: str):
        """
        初始化 Hydra 引擎
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.logger = Logger()
        self.config_loader = ConfigLoader()
        self.config: Dict[str, Any] = {}
        
        # 组件
        self.llm_provider = None
        self.content_strategy = None
        self.template_renderer = None
        self.domain_dispatcher = None
        self.link_mesh = LinkMesh()
        self.seo_builder = SEODataBuilder()
        self.markdown_converter = MarkdownConverter()
    
    def initialize(self):
        """初始化所有组件"""
        # 加载配置
        self.config = self.config_loader.load(self.config_path)
        
        # 配置日志
        log_config = self.config.get("logging", {})
        self.logger.setup(
            log_level=log_config.get("level", "INFO"),
            log_file=log_config.get("file"),
            console_output=log_config.get("console", True)
        )
        
        self.logger.info("=" * 60)
        self.logger.info("Hydra - The Polymorphic SEO Ecosystem")
        self.logger.info("=" * 60)
        
        # 初始化 LLM 提供者
        llm_config = self.config_loader.get_llm_config()
        self.llm_provider = LLMFactory.get_provider(llm_config)
        self.logger.info(f"LLM 提供者: {self.llm_provider.get_provider_name()}")
        
        # 初始化内容策略
        self.content_strategy = MimicryContentStrategy(self.llm_provider)
        
        # 初始化模板渲染器
        self.template_renderer = JinjaRenderer(template_dir="templates")
        
        # 初始化域名分发器
        self.domain_dispatcher = HydraDomainDispatcher()
        
        self.logger.info("所有组件初始化完成")
    
    async def health_check(self):
        """健康检查"""
        self.logger.info("执行健康检查...")
        
        # 检查 LLM 提供者
        if self.llm_provider:
            is_healthy = await self.llm_provider.health_check()
            if not is_healthy:
                self.logger.warning("LLM 提供者健康检查失败")
            else:
                self.logger.info("LLM 提供者健康检查通过")
        
        # 检查模板目录
        template_dir = Path("templates")
        if not template_dir.exists():
            self.logger.warning("模板目录不存在")
        else:
            self.logger.info("模板目录检查通过")
    
    async def generate_content(
        self,
        keyword: str,
        hostname: str,
        mask_context: str = None,
        persona: str = None
    ) -> Dict[str, Any]:
        """
        生成单个内容页面
        
        Args:
            keyword: 目标关键词
            hostname: 主机名
            mask_context: 伪装上下文（如果为 None，使用默认值）
            persona: 人物角色（如果为 None，使用默认值）
            
        Returns:
            包含生成内容的字典
        """
        # 使用默认值
        if mask_context is None:
            mask_context = self.config.get("default_mask_context", "Technology")
        if persona is None:
            persona = self.config.get("default_persona", "Expert")
        
        self.logger.info(f"生成内容: {keyword} @ {hostname}")
        
        # 规划大纲
        context = {
            "mask_context": mask_context,
            "persona": persona
        }
        outline = await self.content_strategy.plan_outline(keyword, context)
        
        # 生成内容
        content = await self.content_strategy.write_content(
            outline=outline,
            target_keyword=keyword,
            mask_context=mask_context,
            persona=persona
        )
        
        # 提取目录
        toc = self.seo_builder.extract_toc_from_content(content)
        
        # 生成作者信息
        author_info = self.seo_builder.generate_author_bio(persona, mask_context)
        
        return {
            "keyword": keyword,
            "hostname": hostname,
            "title": outline.get("title", f"关于{keyword}的专业指南"),
            "content": content,
            "outline": outline,
            "toc": toc,
            "author": author_info,
            "mask_context": mask_context,
            "persona": persona
        }
    
    async def render_page(self, page_data: Dict[str, Any]) -> str:
        """
        渲染页面为 HTML
        
        Args:
            page_data: 页面数据
            
        Returns:
            HTML 内容
        """
        self.logger.info(f"渲染页面: {page_data.get('title')}")
        
        # 转换 Markdown 为 HTML
        markdown_content = page_data.get("content", "")
        html_content = self.markdown_converter.convert(markdown_content)
        self.markdown_converter.reset()  # 重置转换器
        
        # 准备模板上下文
        context = {
            "page_title": page_data.get("title"),
            "page_description": f"专业的{page_data.get('keyword')}指南",
            "article_title": page_data.get("title"),
            "article_content": html_content,  # 使用转换后的 HTML
            "toc": page_data.get("toc", []),
            "author_name": page_data.get("author", {}).get("name", ""),
            "author_bio": page_data.get("author", {}).get("bio", ""),
            "publish_date": "2024-01-01",  # 可以从配置或数据获取
            "last_updated": "2024-01-01",
            "site_name": self.config.get("project_name", "Hydra Site"),
            "breadcrumbs": [
                {"label": "首页", "url": "/"},
                {"label": page_data.get("title", "页面"), "url": "#"}
            ]
        }
        
        # 渲染模板
        html = self.template_renderer.render("article.html", context)
        
        # 构建 SEO 数据
        seo_data = {
            "article": self.seo_builder.build_article_schema(
                title=page_data.get("title"),
                description=context["page_description"],
                author_name=context["author_name"],
                publish_date=context["publish_date"],
                url=f"https://{page_data.get('hostname')}/"
            ),
            "breadcrumbs": self.seo_builder.build_breadcrumb_schema(
                context["breadcrumbs"]
            )
        }
        
        # 注入 SEO 数据
        html = self.template_renderer.inject_seo_data(html, seo_data)
        
        return html
    
    def save_page(self, html: str, hostname: str, path: str = "/"):
        """
        保存页面到文件
        
        Args:
            html: HTML 内容
            hostname: 主机名
            path: URL 路径
        """
        # 解析输出路径
        output_path = self.domain_dispatcher.resolve_path(
            self.config,
            hostname,
            path
        )
        
        # 创建目录
        file_path = Path(output_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        file_path.write_text(html, encoding='utf-8')
        self.logger.info(f"页面已保存: {output_path}")
    
    async def generate_site(self):
        """生成整个站点"""
        self.logger.info("开始生成站点...")
        
        topology = self.domain_dispatcher.get_topology_config(self.config)
        mode = self.config.get("mode", "composite")
        
        if mode == "swarm":
            # Swarm Mode: 为每个关键词生成页面
            keywords = self.config.get("swarm", {}).get("keywords", [])
            base_domain = self.config.get("base_domain", "example.com")
            
            for keyword in keywords:
                # 生成 hostname
                import re
                clean_keyword = re.sub(r'[^\w-]', '', keyword.lower().replace(' ', '-'))
                hostname = f"{clean_keyword}.{base_domain}"
                
                # 生成内容
                page_data = await self.generate_content(
                    keyword=keyword,
                    hostname=hostname
                )
                
                # 渲染页面
                html = await self.render_page(page_data)
                
                # 保存页面
                self.save_page(html, hostname, "/")
        else:
            # Composite Mode: 为每个拓扑配置生成页面
            for topo in topology:
                hostname = topo.get("hostname")
                if not hostname:
                    continue
                
                # 使用配置中的关键词或默认值
                keyword = topo.get("keyword", "专业指南")
                mask_context = topo.get("mask_context", self.config.get("default_mask_context"))
                persona = topo.get("persona", self.config.get("default_persona"))
                
                # 生成内容
                page_data = await self.generate_content(
                    keyword=keyword,
                    hostname=hostname,
                    mask_context=mask_context,
                    persona=persona
                )
                
                # 渲染页面
                html = await self.render_page(page_data)
                
                # 保存页面
                self.save_page(html, hostname, "/")
        
        # 生成 Nginx 配置
        nginx_gen = NginxGenerator()
        nginx_gen.generate_config(
            self.config,
            topology,
            "nginx.conf"
        )
        
        self.logger.info("站点生成完成！")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Hydra - The Polymorphic SEO Ecosystem")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="配置文件路径（默认: config.yaml）"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="仅执行健康检查"
    )
    
    args = parser.parse_args()
    
    # 创建引擎
    engine = HydraEngine(args.config)
    
    try:
        # 初始化
        engine.initialize()
        
        # 健康检查
        await engine.health_check()
        
        if args.health_check:
            sys.exit(0)
        
        # 生成站点
        await engine.generate_site()
        
    except KeyboardInterrupt:
        engine.logger.info("用户中断")
        sys.exit(1)
    except Exception as e:
        engine.logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

