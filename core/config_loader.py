"""
配置加载器
从 YAML 文件加载配置
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from .logger import Logger


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self):
        self.logger = Logger()
        self.config: Optional[Dict[str, Any]] = None
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            self.logger.info(f"成功加载配置文件: {config_path}")
            return self.config
        except yaml.YAMLError as e:
            self.logger.error(f"YAML 解析错误: {e}")
            raise
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键（如 "llm.provider"）
            default: 默认值
            
        Returns:
            配置值
        """
        if self.config is None:
            raise ValueError("配置未加载，请先调用 load()")
        
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        return self.get('llm', {})
    
    def get_topology_config(self) -> List[Dict[str, Any]]:
        """获取域名拓扑配置"""
        return self.get('topology', [])
    
    def get_output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self.get('output', {'path': 'dist'})

