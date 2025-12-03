"""
管道管理器
协调各个组件的工作流程
"""

from typing import Dict, Any, List, Callable, Optional
from .logger import Logger
from .config_loader import ConfigLoader


class Pipeline:
    """管道管理器"""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.logger = Logger()
        self.stages: List[Callable] = []
    
    def add_stage(self, stage: Callable):
        """
        添加处理阶段
        
        Args:
            stage: 处理函数（必须是 async 函数）
        """
        self.stages.append(stage)
        self.logger.debug(f"添加处理阶段: {stage.__name__}")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行管道
        
        Args:
            context: 初始上下文数据
            
        Returns:
            处理后的上下文数据
        """
        self.logger.info("开始执行管道")
        
        for i, stage in enumerate(self.stages, 1):
            self.logger.debug(f"执行阶段 {i}/{len(self.stages)}: {stage.__name__}")
            try:
                context = await stage(context)
            except Exception as e:
                self.logger.error(f"阶段 {stage.__name__} 执行失败: {e}")
                raise
        
        self.logger.info("管道执行完成")
        return context
    
    def clear(self):
        """清空所有阶段"""
        self.stages.clear()
        self.logger.debug("清空所有处理阶段")

