"""
Markdown 转换器
将 Markdown 内容转换为 HTML
"""

import markdown
from typing import Optional
from core.logger import Logger


class MarkdownConverter:
    """Markdown 到 HTML 转换器"""
    
    def __init__(self):
        self.logger = Logger()
        self.md = markdown.Markdown(
            extensions=[
                'extra',  # 包含表格、代码块等
                'codehilite',  # 代码高亮
                'toc',  # 目录生成
                'nl2br',  # 换行转换
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': False
                },
                'toc': {
                    'permalink': True,
                    'baselevel': 2
                }
            }
        )
    
    def convert(self, markdown_text: str) -> str:
        """
        将 Markdown 转换为 HTML
        
        Args:
            markdown_text: Markdown 格式的文本
            
        Returns:
            HTML 格式的文本
        """
        try:
            html = self.md.convert(markdown_text)
            self.logger.debug(f"Markdown 转换完成，长度: {len(html)} 字符")
            return html
        except Exception as e:
            self.logger.error(f"Markdown 转换失败: {e}")
            # 如果转换失败，返回原始文本（转义 HTML）
            import html as html_escape
            return f"<pre>{html_escape.escape(markdown_text)}</pre>"
    
    def reset(self):
        """重置转换器状态（用于多次转换）"""
        self.md.reset()

