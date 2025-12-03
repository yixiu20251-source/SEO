"""
OpenAI LLM 提供者
连接 OpenAI API（或兼容的 API）
"""

import httpx
import os
from typing import Optional, Any
from interfaces.llm_provider import LLMProvider
from core.logger import Logger


class OpenAIProvider(LLMProvider):
    """OpenAI API 提供者"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4"
    ):
        """
        初始化 OpenAI 提供者
        
        Args:
            api_key: API 密钥（如果为 None，从环境变量读取）
            base_url: API 基础 URL（支持兼容 OpenAI 的 API）
            model: 模型名称
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key 未设置，请提供 api_key 或设置 OPENAI_API_KEY 环境变量")
        
        self.base_url = base_url
        self.model = model
        self.logger = Logger()
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=300.0
        )
    
    async def generate(
        self,
        prompt: str,
        system_role: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        使用 OpenAI API 生成文本
        
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
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
            }
            
            self.logger.debug(f"调用 OpenAI API: {self.model}")
            response = await self.client.post(
                "/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            self.logger.debug(f"OpenAI 生成完成，长度: {len(content)} 字符")
            return content
            
        except httpx.HTTPError as e:
            self.logger.error(f"OpenAI API 请求失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"OpenAI 生成失败: {e}")
            raise
    
    async def health_check(self) -> bool:
        """检查 OpenAI API 是否可用"""
        try:
            # 简单的模型列表请求作为健康检查
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"OpenAI 健康检查失败: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """返回提供者名称"""
        return f"OpenAI ({self.model})"
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

