"""
模板混淆器
通过随机化 HTML 结构、CSS 类名和 DOM 节点深度，生成独特的代码指纹
"""

import re
import random
import string
from typing import Dict, Any, Optional
from core.logger import Logger


class TemplateObfuscator:
    """模板混淆器"""
    
    def __init__(self):
        self.logger = Logger()
    
    def generate_fingerprint(self, length: int = 6) -> str:
        """
        生成模板指纹ID
        
        Args:
            length: 指纹长度
            
        Returns:
            指纹字符串（如 "x8d_9s"）
        """
        chars = string.ascii_lowercase + string.digits
        parts = [
            ''.join(random.choices(chars, k=random.randint(2, 4)))
            for _ in range(2)
        ]
        return '_'.join(parts)
    
    def obfuscate_css_class(self, class_name: str, fingerprint: str) -> str:
        """
        混淆 CSS 类名
        
        Args:
            class_name: 原始类名
            fingerprint: 模板指纹
            
        Returns:
            混淆后的类名
        """
        # 生成随机后缀
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(2, 3)))
        
        # 混淆策略：添加指纹和随机字符
        if len(class_name) > 0:
            # 保留部分原始名称，添加混淆
            prefix = class_name[:2] if len(class_name) > 2 else class_name
            return f"{prefix}_{fingerprint[:2]}{random_suffix}"
        else:
            return f"cls_{fingerprint[:2]}{random_suffix}"
    
    def obfuscate_html_structure(self, html: str, fingerprint: str) -> str:
        """
        混淆 HTML 结构
        
        Args:
            html: 原始 HTML
            fingerprint: 模板指纹
            
        Returns:
            混淆后的 HTML
        """
        # 创建类名映射
        class_map: Dict[str, str] = {}
        
        # 提取所有 CSS 类名
        class_pattern = r'class=["\']([^"\']+)["\']'
        
        def replace_class(match):
            original_classes = match.group(1)
            classes = original_classes.split()
            obfuscated_classes = []
            
            for cls in classes:
                if cls not in class_map:
                    class_map[cls] = self.obfuscate_css_class(cls, fingerprint)
                obfuscated_classes.append(class_map[cls])
            
            return f'class="{" ".join(obfuscated_classes)}"'
        
        # 替换类名
        html = re.sub(class_pattern, replace_class, html)
        
        # 添加随机注释
        if random.random() > 0.5:
            comment = f"<!-- {self.generate_fingerprint(8)} -->"
            # 在 body 开始后添加
            html = re.sub(r'(<body[^>]*>)', rf'\1\n{comment}\n', html, count=1, flags=re.IGNORECASE)
        
        # 随机化 ID 属性
        id_pattern = r'id=["\']([^"\']+)["\']'
        def replace_id(match):
            original_id = match.group(1)
            random_suffix = ''.join(random.choices(string.digits, k=random.randint(3, 5)))
            return f'id="{original_id}_{random_suffix}"'
        
        html = re.sub(id_pattern, replace_id, html)
        
        # 添加随机空白节点（在某些位置）
        if random.random() > 0.7:
            spacer = f'<div class="spacer-{random.randint(10, 99)}"></div>'
            # 在第一个 div 后添加
            html = re.sub(r'(<div[^>]*>)', rf'\1\n{spacer}\n', html, count=1, flags=re.IGNORECASE)
        
        return html
    
    def generate_template_variant(
        self,
        base_html: str,
        fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成模板变体
        
        Args:
            base_html: 基础 HTML 模板
            fingerprint: 可选的指纹（如果不提供则自动生成）
            
        Returns:
            包含混淆后 HTML 和指纹的字典
        """
        if fingerprint is None:
            fingerprint = self.generate_fingerprint()
        
        obfuscated_html = self.obfuscate_html_structure(base_html, fingerprint)
        
        return {
            "fingerprint": fingerprint,
            "html": obfuscated_html,
            "original_length": len(base_html),
            "obfuscated_length": len(obfuscated_html)
        }
    
    def compare_templates(self, html1: str, html2: str) -> Dict[str, Any]:
        """
        比较两个模板的相似度
        
        Args:
            html1: 第一个 HTML
            html2: 第二个 HTML
            
        Returns:
            相似度分析结果
        """
        # 提取类名
        def extract_classes(html):
            pattern = r'class=["\']([^"\']+)["\']'
            classes = set()
            for match in re.finditer(pattern, html):
                classes.update(match.group(1).split())
            return classes
        
        classes1 = extract_classes(html1)
        classes2 = extract_classes(html2)
        
        # 计算相似度
        intersection = classes1 & classes2
        union = classes1 | classes2
        similarity = len(intersection) / len(union) if union else 0
        
        return {
            "similarity": similarity,
            "common_classes": len(intersection),
            "total_classes": len(union),
            "unique_to_1": len(classes1 - classes2),
            "unique_to_2": len(classes2 - classes1)
        }

