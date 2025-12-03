"""
提示词构建器
使用 Jinja2 模板构建包含 Context Masking 的提示词
"""

from jinja2 import Template
from typing import Dict, Any
from core.logger import Logger


class PromptBuilder:
    """提示词构建器"""
    
    # 系统角色模板
    SYSTEM_ROLE_TEMPLATE = """你是一位{{ persona }}，在{{ mask_context }}领域拥有{{ years }}年的专业经验。
你的专业知识包括：
- {{ expertise_areas }}

你的写作风格：
- 专业、权威、可信
- 使用行业术语和标准表达
- 提供实用的、可操作的建议
- 引用真实案例和数据（可以合理虚构但需符合逻辑）

请始终以{{ persona }}的身份和视角来撰写内容。"""
    
    # 内容生成提示词模板
    CONTENT_PROMPT_TEMPLATE = """请撰写一篇关于"{{ topic }}"的专业文章。

**重要要求：**
1. 文章主题必须围绕{{ mask_context }}领域
2. 在文章中，将"{{ target_keyword }}"作为以下形式之一自然地融入：
   - 产品型号或技术术语（如："{{ target_keyword }}-2000 系列"）
   - 内部变量名或代码标识符（如："{{ target_keyword }}_module"）
   - 隐喻或类比（如："就像{{ target_keyword }}一样高效"）
   - 特定场景下的专业术语

3. 确保文章内容在{{ mask_context }}领域内完全合理和可信
4. 文章结构：
   - 引人入胜的开头
   - 清晰的小标题（H2, H3）
   - 详细的正文内容
   - 实用的建议或总结

5. 字数要求：{{ word_count }}字左右
6. 使用Markdown格式，包含适当的标题层级

**大纲：**
{{ outline }}

请开始撰写："""
    
    def __init__(self):
        self.logger = Logger()
        self.system_template = Template(self.SYSTEM_ROLE_TEMPLATE)
        self.content_template = Template(self.CONTENT_PROMPT_TEMPLATE)
    
    def build_system_role(
        self,
        persona: str,
        mask_context: str,
        years: int = 10,
        expertise_areas: str = "相关技术、市场趋势、最佳实践"
    ) -> str:
        """
        构建系统角色提示词
        
        Args:
            persona: 人物角色（如 "Senior Engineer"）
            mask_context: 伪装上下文（如 "Industrial Machinery"）
            years: 经验年数
            expertise_areas: 专业领域描述
            
        Returns:
            系统角色提示词
        """
        try:
            role = self.system_template.render(
                persona=persona,
                mask_context=mask_context,
                years=years,
                expertise_areas=expertise_areas
            )
            self.logger.debug(f"构建系统角色: {persona} in {mask_context}")
            return role
        except Exception as e:
            self.logger.error(f"构建系统角色失败: {e}")
            raise
    
    def build_content_prompt(
        self,
        topic: str,
        target_keyword: str,
        mask_context: str,
        outline: Dict[str, Any],
        word_count: int = 2000
    ) -> str:
        """
        构建内容生成提示词
        
        Args:
            topic: 文章主题
            target_keyword: 目标关键词（需要伪装）
            mask_context: 伪装上下文
            outline: 内容大纲
            word_count: 目标字数
            
        Returns:
            内容生成提示词
        """
        try:
            # 将大纲转换为字符串
            outline_str = self._format_outline(outline)
            
            prompt = self.content_template.render(
                topic=topic,
                target_keyword=target_keyword,
                mask_context=mask_context,
                outline=outline_str,
                word_count=word_count
            )
            
            self.logger.debug(f"构建内容提示词: {topic} (伪装: {mask_context})")
            return prompt
        except Exception as e:
            self.logger.error(f"构建内容提示词失败: {e}")
            raise
    
    def _format_outline(self, outline: Dict[str, Any]) -> str:
        """
        格式化大纲为字符串
        
        Args:
            outline: 大纲字典
            
        Returns:
            格式化后的大纲字符串
        """
        if isinstance(outline, str):
            return outline
        
        if isinstance(outline, dict):
            sections = []
            for key, value in outline.items():
                if isinstance(value, list):
                    sections.append(f"- {key}:")
                    for item in value:
                        sections.append(f"  - {item}")
                else:
                    sections.append(f"- {key}: {value}")
            return "\n".join(sections)
        
        return str(outline)

