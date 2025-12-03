"""
Ollama LLM 提供者
连接本地 Ollama 服务（localhost:11434）
"""

import httpx
from typing import Optional, Any, Dict
from interfaces.llm_provider import LLMProvider
from core.logger import Logger


class OllamaProvider(LLMProvider):
    """Ollama 本地 LLM 提供者"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        """
        初始化 Ollama 提供者
        
        Args:
            base_url: Ollama API 地址
            model: 模型名称
        """
        self.base_url = base_url
        self.model = model
        self.logger = Logger()
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def generate(
        self,
        prompt: str,
        system_role: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        使用 Ollama 生成文本
        
        Args:
            prompt: 用户提示词
            system_role: 系统角色提示
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            生成的文本内容
        """
        try:
            messages = []
            
            if system_role:
                messages.append({
                    "role": "system",
                    "content": system_role
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 2048),
                }
            }
            
            self.logger.debug(f"调用 Ollama API: {self.base_url}/api/chat")
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            self.logger.debug(f"Ollama 生成完成，长度: {len(content)} 字符")
            return content
            
        except httpx.HTTPError as e:
            self.logger.error(f"Ollama API 请求失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Ollama 生成失败: {e}")
            raise
    
    async def health_check(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama 健康检查失败: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """返回提供者名称"""
        return f"Ollama ({self.model})"
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

