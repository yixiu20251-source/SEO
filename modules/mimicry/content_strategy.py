"""
模仿内容策略
实现 ContentStrategy 接口，使用 Context Masking 生成内容
"""

from typing import Dict, Any
from interfaces.content_strategy import ContentStrategy
from interfaces.llm_provider import LLMProvider
from modules.mimicry.prompt_builder import PromptBuilder
from core.logger import Logger


class MimicryContentStrategy(ContentStrategy):
    """模仿内容策略实现"""
    
    def __init__(self, llm_provider: LLMProvider):
        """
        初始化模仿内容策略
        
        Args:
            llm_provider: LLM 提供者实例
        """
        self.llm_provider = llm_provider
        self.prompt_builder = PromptBuilder()
        self.logger = Logger()
    
    async def plan_outline(self, keyword: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        规划内容大纲
        
        Args:
            keyword: 目标关键词
            context: 上下文信息（mask_context, persona 等）
            
        Returns:
            包含大纲结构的字典
        """
        mask_context = context.get("mask_context", "Technology")
        persona = context.get("persona", "Expert")
        
        # 构建大纲规划提示词
        outline_prompt = f"""请为以下主题规划一篇专业文章的大纲：

主题：在{mask_context}领域中，关于"{keyword}"的专业文章

要求：
1. 提供3-5个主要章节（H2级别）
2. 每个章节包含2-3个子章节（H3级别）
3. 确保大纲逻辑清晰，层次分明
4. 大纲应该符合{mask_context}领域的专业标准

请以JSON格式返回大纲，格式如下：
{{
  "title": "文章标题",
  "sections": [
    {{
      "heading": "章节标题",
      "subsections": ["子章节1", "子章节2"]
    }}
  ]
}}"""
        
        try:
            self.logger.info(f"规划内容大纲: {keyword} (伪装: {mask_context})")
            
            # 使用 LLM 生成大纲
            outline_text = await self.llm_provider.generate(
                prompt=outline_prompt,
                system_role=f"你是一位{mask_context}领域的{persona}，擅长规划专业文章结构。"
            )
            
            # 使用正则表达式提取 JSON（更健壮的方法）
            import json
            import re
            
            # 尝试多种方法提取 JSON
            outline_json = None
            
            # 方法1: 尝试直接解析整个文本
            try:
                outline_json = json.loads(outline_text)
            except json.JSONDecodeError:
                pass
            
            # 方法2: 使用正则表达式匹配 JSON 对象
            if outline_json is None:
                # 匹配嵌套的 JSON 对象（支持简单嵌套）
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                matches = re.findall(json_pattern, outline_text, re.DOTALL)
                
                for match in matches:
                    try:
                        outline_json = json.loads(match)
                        break
                    except json.JSONDecodeError:
                        continue
            
            # 方法3: 尝试提取第一个 { 到最后一个 } 之间的内容
            if outline_json is None:
                json_start = outline_text.find('{')
                json_end = outline_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    try:
                        outline_json = json.loads(outline_text[json_start:json_end])
                    except json.JSONDecodeError:
                        pass
            
            if outline_json:
                return outline_json
            else:
                # 如果所有方法都失败，返回默认结构
                self.logger.warning("无法解析 JSON 大纲，使用默认结构")
                return {
                    "title": f"关于{keyword}的专业指南",
                    "sections": [
                        {"heading": "概述", "subsections": ["简介", "重要性"]},
                        {"heading": "核心内容", "subsections": ["主要特点", "应用场景"]},
                        {"heading": "总结", "subsections": ["要点回顾", "未来展望"]}
                    ]
                }
        except Exception as e:
            self.logger.error(f"规划大纲失败: {e}")
            # 返回默认大纲
            return {
                "title": f"关于{keyword}的专业指南",
                "sections": [
                    {"heading": "概述", "subsections": ["简介", "重要性"]},
                    {"heading": "核心内容", "subsections": ["主要特点", "应用场景"]},
                    {"heading": "总结", "subsections": ["要点回顾", "未来展望"]}
                ]
            }
    
    async def write_content(
        self,
        outline: Dict[str, Any],
        target_keyword: str,
        mask_context: str,
        persona: str
    ) -> str:
        """
        根据大纲生成完整内容
        
        Args:
            outline: 内容大纲
            target_keyword: 目标关键词（需要伪装）
            mask_context: 伪装上下文（如 "Industrial Machinery"）
            persona: 人物角色（如 "Senior Engineer"）
            
        Returns:
            生成的完整内容（Markdown 格式）
        """
        try:
            self.logger.info(f"生成内容: {target_keyword} (伪装: {mask_context})")
            
            # 构建系统角色
            system_role = self.prompt_builder.build_system_role(
                persona=persona,
                mask_context=mask_context
            )
            
            # 构建内容提示词
            topic = outline.get("title", f"关于{target_keyword}的专业指南")
            content_prompt = self.prompt_builder.build_content_prompt(
                topic=topic,
                target_keyword=target_keyword,
                mask_context=mask_context,
                outline=outline
            )
            
            # 使用 LLM 生成内容
            content = await self.llm_provider.generate(
                prompt=content_prompt,
                system_role=system_role,
                temperature=0.8,
                max_tokens=4000
            )
            
            self.logger.info(f"内容生成完成，长度: {len(content)} 字符")
            return content
            
        except Exception as e:
            self.logger.error(f"生成内容失败: {e}")
            raise
    
    def get_strategy_name(self) -> str:
        """返回策略名称"""
        return "MimicryContentStrategy"

