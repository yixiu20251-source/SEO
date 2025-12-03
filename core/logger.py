"""
日志管理器
提供统一的日志记录功能
"""

import logging
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path


class Logger:
    """统一的日志管理器"""
    
    _instance: Optional['Logger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = logging.getLogger('hydra')
            self.logger.setLevel(logging.DEBUG)
            self._initialized = True
    
    def setup(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        console_output: bool = True
    ):
        """
        配置日志系统
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 日志文件路径（可选）
            console_output: 是否输出到控制台
        """
        self.logger.handlers.clear()
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """记录 DEBUG 级别日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录 INFO 级别日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录 WARNING 级别日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录 ERROR 级别日志"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录 CRITICAL 级别日志"""
        self.logger.critical(message)

