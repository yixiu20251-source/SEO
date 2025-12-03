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
from plugins.domain.cloudflare_manager import CloudflareManager

# 导入业务逻辑
from modules.mimicry.content_strategy import MimicryContentStrategy
from modules.seo.link_mesh import LinkMesh
from modules.seo.traffic_filter import TrafficFilter
from modules.seo.seo_data_builder import SEODataBuilder
from modules.seo.nginx_generator import NginxGenerator
from modules.content.markdown_converter import MarkdownConverter


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
        self.traffic_filter = None  # 将在 initialize 中根据配置初始化
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
        
        # 初始化流量过滤器
        landing_page = self.config.get("seo", {}).get("landing_page", "/")
        self.traffic_filter = TrafficFilter(landing_page=landing_page)
        self.logger.info(f"流量过滤器已初始化，着陆页: {landing_page}")
        
        self.logger.info("所有组件初始化完成")
    
    async def shutdown(self):
        """
        关闭所有资源，清理HTTP客户端连接
        
        应该在程序退出前调用此方法以确保资源正确释放
        """
        self.logger.info("正在关闭资源...")
        
        # 关闭 LLM 提供者的 HTTP 客户端
        if self.llm_provider and hasattr(self.llm_provider, 'client'):
            try:
                await self.llm_provider.client.aclose()
                self.logger.info("LLM 提供者 HTTP 客户端已关闭")
            except Exception as e:
                self.logger.warning(f"关闭 LLM 提供者客户端时出错: {e}")
        
        self.logger.info("资源关闭完成")
    
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
    
    async def render_page(
        self, 
        page_data: Dict[str, Any], 
        related_links: List[Dict[str, Any]] = None
    ) -> str:
        """
        渲染页面为 HTML
        
        Args:
            page_data: 页面数据
            related_links: 相关链接列表（从 LinkMesh 生成）
            
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
            ],
            "related_links": related_links or []  # 添加相关链接
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
    
    def _plan_pages(self) -> List[Dict[str, Any]]:
        """
        Pass 1: 规划阶段 - 收集所有页面信息并注册到 LinkMesh
        
        Returns:
            页面规划列表，每个元素包含 url, hostname, keyword, mask_context 等
        """
        self.logger.info("=" * 60)
        self.logger.info("Pass 1: 规划阶段 - 注册所有页面到链接网络")
        self.logger.info("=" * 60)
        
        topology = self.domain_dispatcher.get_topology_config(self.config)
        mode = self.config.get("mode", "composite")
        page_plans: List[Dict[str, Any]] = []
        
        if mode == "swarm":
            # Swarm Mode: 为每个关键词规划页面
            keywords = self.config.get("swarm", {}).get("keywords", [])
            base_domain = self.config.get("base_domain", "example.com")
            default_mask_context = self.config.get("default_mask_context", "Technology")
            
            for keyword in keywords:
                # 生成 hostname
                import re
                clean_keyword = re.sub(r'[^\w-]', '', keyword.lower().replace(' ', '-'))
                hostname = f"{clean_keyword}.{base_domain}"
                url = f"https://{hostname}/"
                
                # 注册到 LinkMesh
                self.link_mesh.add_page(url, default_mask_context)
                
                # 保存规划信息
                page_plans.append({
                    "url": url,
                    "hostname": hostname,
                    "keyword": keyword,
                    "mask_context": default_mask_context,
                    "persona": self.config.get("default_persona", "Expert"),
                    "path": "/"
                })
                
                self.logger.debug(f"规划页面: {url} (上下文: {default_mask_context})")
        else:
            # Composite Mode: 为每个拓扑配置规划页面
            for topo in topology:
                hostname = topo.get("hostname")
                if not hostname:
                    continue
                
                url = f"https://{hostname}/"
                keyword = topo.get("keyword", "专业指南")
                mask_context = topo.get(
                    "mask_context", 
                    self.config.get("default_mask_context", "Technology")
                )
                persona = topo.get(
                    "persona", 
                    self.config.get("default_persona", "Expert")
                )
                
                # 注册到 LinkMesh
                self.link_mesh.add_page(url, mask_context)
                
                # 保存规划信息
                page_plans.append({
                    "url": url,
                    "hostname": hostname,
                    "keyword": keyword,
                    "mask_context": mask_context,
                    "persona": persona,
                    "path": "/"
                })
                
                self.logger.debug(f"规划页面: {url} (上下文: {mask_context})")
        
        self.logger.info(f"规划完成: 共 {len(page_plans)} 个页面")
        return page_plans
    
    async def generate_site(self):
        """生成整个站点（两阶段生成）"""
        self.logger.info("开始生成站点...")
        
        # Pass 1: 规划阶段
        page_plans = self._plan_pages()
        
        # Pass 2: 生成阶段（并发）
        self.logger.info("=" * 60)
        self.logger.info("Pass 2: 生成阶段 - 生成内容和链接（并发模式）")
        self.logger.info("=" * 60)
        
        # 创建信号量限制并发数（最多5个并发任务）
        semaphore = asyncio.Semaphore(5)
        
        async def generate_content_worker(plan: Dict[str, Any]) -> Dict[str, Any]:
            """并发工作函数：生成单个页面内容"""
            async with semaphore:
                try:
                    # 生成内容
                    page_data = await self.generate_content(
                        keyword=plan["keyword"],
                        hostname=plan["hostname"],
                        mask_context=plan["mask_context"],
                        persona=plan["persona"]
                    )
                    
                    # 添加 URL 到页面数据
                    page_data["url"] = plan["url"]
                    return page_data
                except Exception as e:
                    self.logger.error(f"生成页面内容失败 {plan.get('url', 'unknown')}: {e}")
                    raise
        
        # 并发生成所有页面内容
        self.logger.info(f"开始并发生成 {len(page_plans)} 个页面...")
        content_tasks = [generate_content_worker(plan) for plan in page_plans]
        generated_pages = await asyncio.gather(*content_tasks, return_exceptions=True)
        
        # 处理异常结果
        valid_pages: List[Dict[str, Any]] = []
        all_pages_metadata: List[Dict[str, Any]] = []
        
        for i, result in enumerate(generated_pages):
            if isinstance(result, Exception):
                self.logger.error(f"页面生成失败: {page_plans[i].get('url', 'unknown')}, 错误: {result}")
                continue
            
            valid_pages.append(result)
            
            # 收集页面元数据（用于链接生成）
            all_pages_metadata.append({
                "url": result["url"],
                "title": result.get("title"),
                "mask_context": page_plans[i]["mask_context"],
                "hostname": page_plans[i]["hostname"]
            })
        
        self.logger.info(f"内容生成完成: {len(valid_pages)}/{len(page_plans)} 个页面成功")
        
        # Pass 3: 链接生成和渲染阶段（并发）
        self.logger.info("=" * 60)
        self.logger.info("Pass 3: 链接生成和渲染阶段（并发模式）")
        self.logger.info("=" * 60)
        
        async def render_page_worker(plan: Dict[str, Any], page_data: Dict[str, Any]) -> None:
            """并发工作函数：生成链接并渲染页面"""
            async with semaphore:
                try:
                    # 生成上下文相关的链接
                    max_links = self.config.get("seo", {}).get("max_internal_links", 5)
                    related_links = self.link_mesh.generate_contextual_links(
                        current_url=plan["url"],
                        all_pages=all_pages_metadata,
                        max_links=max_links
                    )
                    
                    # 转换链接格式为模板需要的格式
                    formatted_links = [
                        {
                            "url": link["url"],
                            "title": link["title"],
                            "description": f"了解更多关于 {link.get('title', '')} 的信息"
                        }
                        for link in related_links
                    ]
                    
                    # 渲染页面（包含相关链接）
                    html = await self.render_page(page_data, related_links=formatted_links)
                    
                    # 保存页面
                    self.save_page(html, plan["hostname"], plan["path"])
                except Exception as e:
                    self.logger.error(f"渲染页面失败 {plan.get('url', 'unknown')}: {e}")
                    raise
        
        # 并发渲染所有页面
        self.logger.info(f"开始并发渲染 {len(valid_pages)} 个页面...")
        render_tasks = [
            render_page_worker(page_plans[i], valid_pages[i])
            for i in range(len(valid_pages))
        ]
        await asyncio.gather(*render_tasks, return_exceptions=True)
        
        self.logger.info("页面渲染完成")
        
        # Cloudflare DNS 自动化（如果启用）
        cloudflare_config = self.config.get("cloudflare", {})
        if cloudflare_config.get("enabled", False):
            await self._setup_cloudflare_dns(page_plans, cloudflare_config)
        
        # 生成 Nginx 配置
        topology = self.domain_dispatcher.get_topology_config(self.config)
        nginx_gen = NginxGenerator()
        
        # 获取 TrafficFilter 的 404 处理配置
        nginx_404_handler = self.traffic_filter.generate_nginx_404_handler()
        
        nginx_gen.generate_config(
            self.config,
            topology,
            "nginx.conf",
            traffic_filter=self.traffic_filter,
            extra_conf=nginx_404_handler
        )
        
        self.logger.info("站点生成完成！")
    
    async def _setup_cloudflare_dns(
        self,
        page_plans: List[Dict[str, Any]],
        cloudflare_config: Dict[str, Any]
    ):
        """
        设置 Cloudflare DNS 记录
        
        Args:
            page_plans: 页面规划列表
            cloudflare_config: Cloudflare 配置
        """
        self.logger.info("=" * 60)
        self.logger.info("Cloudflare DNS 自动化")
        self.logger.info("=" * 60)
        
        try:
            api_token = cloudflare_config.get("api_token")
            zone_id = cloudflare_config.get("zone_id")
            email = cloudflare_config.get("email")
            server_ip = cloudflare_config.get("server_ip")
            proxied = cloudflare_config.get("proxied", True)
            
            if not all([api_token, zone_id, email, server_ip]):
                self.logger.warning("Cloudflare 配置不完整，跳过 DNS 设置")
                return
            
            async with CloudflareManager(api_token, zone_id, email) as cf_manager:
                # 健康检查
                if not await cf_manager.health_check():
                    self.logger.error("Cloudflare API 连接失败")
                    return
                
                # 收集唯一的 hostname
                unique_hostnames = set()
                for plan in page_plans:
                    hostname = plan.get("hostname")
                    if hostname:
                        unique_hostnames.add(hostname)
                
                # 为每个唯一的 hostname 创建 DNS 记录
                for hostname in unique_hostnames:
                    success = await cf_manager.add_dns_record(
                        hostname=hostname,
                        ip_address=server_ip,
                        proxied=proxied
                    )
                    if success:
                        self.logger.info(f"✓ DNS 记录已设置: {hostname}")
                    else:
                        self.logger.warning(f"✗ DNS 记录设置失败: {hostname}")
                
                self.logger.info(f"Cloudflare DNS 设置完成: {len(unique_hostnames)} 个记录")
                
        except Exception as e:
            self.logger.error(f"Cloudflare DNS 设置异常: {e}", exc_info=True)


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
            return
        
        # 生成站点
        await engine.generate_site()
        
    except KeyboardInterrupt:
        engine.logger.info("用户中断")
    except Exception as e:
        engine.logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # 确保资源被正确关闭
        await engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

