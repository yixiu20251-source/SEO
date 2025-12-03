"""
SEO 数据构建器
生成 JSON-LD 结构化数据
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from core.logger import Logger


class SEODataBuilder:
    """SEO 结构化数据构建器"""
    
    def __init__(self):
        self.logger = Logger()
    
    def build_article_schema(
        self,
        title: str,
        description: str,
        author_name: str,
        publish_date: str,
        url: str,
        image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建 Article 结构化数据
        
        Args:
            title: 文章标题
            description: 文章描述
            author_name: 作者名称
            publish_date: 发布日期
            url: 文章URL
            image: 文章图片（可选）
            
        Returns:
            Article 结构化数据字典
        """
        schema = {
            "headline": title,
            "description": description,
            "author": {
                "@type": "Person",
                "name": author_name
            },
            "datePublished": publish_date,
            "dateModified": publish_date,
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url
            }
        }
        
        if image:
            schema["image"] = image
        
        return schema
    
    def build_breadcrumb_schema(self, breadcrumbs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        构建 BreadcrumbList 结构化数据
        
        Args:
            breadcrumbs: 面包屑列表，每个元素包含 {label, url}
            
        Returns:
            BreadcrumbList 结构化数据字典
        """
        items = []
        for i, crumb in enumerate(breadcrumbs, 1):
            items.append({
                "@type": "ListItem",
                "position": i,
                "name": crumb.get("label", ""),
                "item": crumb.get("url", "")
            })
        
        return {
            "itemListElement": items
        }
    
    def build_howto_schema(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        构建 HowTo 结构化数据
        
        Args:
            name: 操作名称
            description: 操作描述
            steps: 步骤列表，每个元素包含 {name, text}
            
        Returns:
            HowTo 结构化数据字典
        """
        howto_steps = []
        for i, step in enumerate(steps, 1):
            howto_steps.append({
                "@type": "HowToStep",
                "position": i,
                "name": step.get("name", f"步骤 {i}"),
                "text": step.get("text", "")
            })
        
        return {
            "name": name,
            "description": description,
            "step": howto_steps
        }
    
    def generate_author_bio(self, persona: str, mask_context: str) -> Dict[str, str]:
        """
        生成作者简介
        
        Args:
            persona: 人物角色
            mask_context: 伪装上下文
            
        Returns:
            包含 name 和 bio 的字典
        """
        # 这里可以扩展为更复杂的生成逻辑
        name = f"{persona} ({mask_context})"
        bio = f"在{mask_context}领域拥有丰富经验的{persona}，专注于提供专业的技术见解和实用建议。"
        
        return {
            "name": name,
            "bio": bio
        }
    
    def extract_toc_from_content(self, content: str) -> List[Dict[str, Any]]:
        """
        从 Markdown 内容中提取目录
        
        Args:
            content: Markdown 格式的内容
            
        Returns:
            目录项列表，每个元素包含 {id, title, level}
        """
        import re
        toc = []
        lines = content.split('\n')
        
        for line in lines:
            # 匹配 Markdown 标题 (# ## ###)
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                # 生成 ID（移除特殊字符，转为小写，空格替换为-）
                heading_id = re.sub(r'[^\w\s-]', '', title).lower().replace(' ', '-')
                toc.append({
                    "id": heading_id,
                    "title": title,
                    "level": level
                })
        
        return toc

