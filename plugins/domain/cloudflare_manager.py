"""
Cloudflare 管理器
自动化 DNS 记录管理和 SSL 配置
"""

import httpx
from typing import Optional, Dict, Any
from core.logger import Logger


class CloudflareManager:
    """Cloudflare API 管理器"""
    
    BASE_URL = "https://api.cloudflare.com/client/v4"
    
    def __init__(self, api_token: str, zone_id: str, email: str):
        """
        初始化 Cloudflare 管理器
        
        Args:
            api_token: Cloudflare API Token
            zone_id: Zone ID
            email: Cloudflare 账户邮箱
        """
        self.api_token = api_token
        self.zone_id = zone_id
        self.email = email
        self.logger = Logger()
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_token}",
                "X-Auth-Email": email,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def add_dns_record(
        self,
        hostname: str,
        ip_address: str,
        proxied: bool = True
    ) -> bool:
        """
        添加或更新 DNS A 记录
        
        Args:
            hostname: 主机名（如 example.com 或 sub.example.com）
            ip_address: IP 地址
            proxied: 是否通过 Cloudflare 代理
            
        Returns:
            True 如果成功，否则 False
        """
        try:
            # 首先检查记录是否已存在
            existing_record = await self._get_existing_record(hostname)
            
            if existing_record:
                # 检查 IP 是否改变
                if existing_record.get("content") == ip_address:
                    self.logger.info(f"DNS 记录已存在且 IP 未改变: {hostname} -> {ip_address}")
                    return True
                else:
                    # 更新现有记录
                    record_id = existing_record.get("id")
                    return await self._update_dns_record(record_id, hostname, ip_address, proxied)
            else:
                # 创建新记录
                return await self._create_dns_record(hostname, ip_address, proxied)
                
        except Exception as e:
            self.logger.error(f"添加 DNS 记录失败 {hostname}: {e}")
            return False
    
    async def _get_existing_record(self, hostname: str) -> Optional[Dict[str, Any]]:
        """
        获取现有的 DNS 记录
        
        Args:
            hostname: 主机名
            
        Returns:
            记录字典，如果不存在则返回 None
        """
        try:
            response = await self.client.get(
                f"/zones/{self.zone_id}/dns_records",
                params={
                    "type": "A",
                    "name": hostname
                }
            )
            response.raise_for_status()
            
            result = response.json()
            records = result.get("result", [])
            
            if records:
                return records[0]
            return None
            
        except Exception as e:
            self.logger.warning(f"查询 DNS 记录失败 {hostname}: {e}")
            return None
    
    async def _create_dns_record(
        self,
        hostname: str,
        ip_address: str,
        proxied: bool
    ) -> bool:
        """
        创建新的 DNS A 记录
        
        Args:
            hostname: 主机名
            ip_address: IP 地址
            proxied: 是否代理
            
        Returns:
            True 如果成功
        """
        try:
            payload = {
                "type": "A",
                "name": hostname,
                "content": ip_address,
                "ttl": 1,  # 自动 TTL
                "proxied": proxied
            }
            
            response = await self.client.post(
                f"/zones/{self.zone_id}/dns_records",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("success"):
                self.logger.info(f"成功创建 DNS 记录: {hostname} -> {ip_address} (代理: {proxied})")
                return True
            else:
                errors = result.get("errors", [])
                self.logger.error(f"创建 DNS 记录失败: {errors}")
                return False
                
        except Exception as e:
            self.logger.error(f"创建 DNS 记录异常 {hostname}: {e}")
            return False
    
    async def _update_dns_record(
        self,
        record_id: str,
        hostname: str,
        ip_address: str,
        proxied: bool
    ) -> bool:
        """
        更新现有的 DNS 记录
        
        Args:
            record_id: 记录 ID
            hostname: 主机名
            ip_address: 新 IP 地址
            proxied: 是否代理
            
        Returns:
            True 如果成功
        """
        try:
            payload = {
                "type": "A",
                "name": hostname,
                "content": ip_address,
                "ttl": 1,
                "proxied": proxied
            }
            
            response = await self.client.put(
                f"/zones/{self.zone_id}/dns_records/{record_id}",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("success"):
                self.logger.info(f"成功更新 DNS 记录: {hostname} -> {ip_address}")
                return True
            else:
                errors = result.get("errors", [])
                self.logger.error(f"更新 DNS 记录失败: {errors}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新 DNS 记录异常 {hostname}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """
        检查 Cloudflare API 连接
        
        Returns:
            True 如果连接正常
        """
        try:
            response = await self.client.get(f"/zones/{self.zone_id}")
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except Exception as e:
            self.logger.warning(f"Cloudflare 健康检查失败: {e}")
            return False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

