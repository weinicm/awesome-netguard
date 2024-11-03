import asyncio
import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import fields
from domain.managers.provider_manager import ProviderManager
from domain.managers.ip_manager import IpaddressManager
from domain.models.provider import Provider  # 假设 Provider 模型在 domain/models/provider.py 文件中定义
from schemas.provider import (
    ProviderCreate,
    ProviderUpdate,
    ProviderUpdateCurl,
    ProviderUpdateMonitor,
    ProviderUpdateTcping,
)
from domain.managers.ip_range_manager import IPRangeManager
import json

class ProviderService:
    def __init__(self):
        self.provider_manager = ProviderManager()
        self.ip_range_manager = IPRangeManager()
        self.ip_manager = IpaddressManager()

    async def get_providers(self) -> List[Provider]:
        """获取所有供应商"""
        providers = await self.provider_manager.get_providers()
        for provider in providers:
            ip_ranges = await self.ip_range_manager.get_ip_ranges_by_provider_id(provider.id)
            provider.ip_ranges = ip_ranges
        return providers


    async def get_provider_by_name(self, name: str) -> Optional[Provider]:
        """根据名称获取供应商"""
        return await self.provider_manager.get_provider_by_name(name)

    async def get_provider_by_id(self, provider_id: int) -> Optional[Provider]:
        """根据ID获取供应商"""
        return await self.provider_manager.get_provider_by_id(provider_id)

    async def get_provider_config(self, provider_id: int) -> Optional[Dict]:
        """获取供应商的配置信息"""
        return await self.provider_manager.get_provider_config(provider_id)
    
    async def get_tcping_config(self, provider_id: int) -> Optional[Dict]:
        """获取供应商的TCPing配置"""
        config = await self.get_provider_config(provider_id)
        if config and 'tcping' in config:
            return config['tcping']
        return None

    async def get_curl_config(self, provider_id: int) -> Optional[Dict]:
        """获取供应商的Curl配置"""
        config = await self.get_provider_config(provider_id)
        if config and 'curl' in config:
            return config['curl']
        return None

    async def get_monitor_config(self, provider_id: int) -> Optional[Dict]:
        """获取供应商的监控配置"""
        config = await self.get_provider_config(provider_id)
        if config and 'monitor' in config:
            return config['monitor']
        return None

    async def create_provider(self, provider_data: ProviderCreate) -> Provider:
        """创建新的供应商"""
        provider_dict = provider_data.model_dump()
        # 在这里进行二次加工
        # 例如：provider_dict['some_field'] = some_function(provider_dict['another_field'])
        return await self.provider_manager.create_provider(provider_dict)

    async def update_provider(self, provider_id: int, provider_data: ProviderUpdate) -> Optional[Provider]:
        """更新供应商的基本信息"""
        provider_dict = provider_data.model_dump()
        return await self.provider_manager.update_provider(provider_id, provider_dict)

    async def update_provider_fields(self, provider_id: int, provider_data: ProviderUpdate) -> Optional[Provider]:
        """更新供应商的指定字段"""
        # 获取需要更新的字段
        update_dict = provider_data.model_dump(exclude_unset=True)
        logging.info(f"Updating provider fields: {update_dict}")

        # 获取 Provider 数据类的所有字段名
        valid_fields = {f.name for f in fields(Provider)}
        # 检查每个字段是否有效
        for field in update_dict.keys():
            if field not in valid_fields:
                raise ValueError(f"Field '{field}' is not a valid field in the Provider model.")

        # 只更新指定的字段
        return await self.provider_manager.update_provider_fields(provider_id, update_dict)


    async def update_provider_tcping(self, provider_id: int, tcping_data: ProviderUpdateTcping) -> Optional[Provider]:
        """更新供应商的TCPing设置"""
        current_provider = await self.get_provider_by_id(provider_id)
        if current_provider is None:
            logging.warning(f"Provider with ID {provider_id} not found.")
            return None

        # 获取当前配置
        config = current_provider.config or {}
        
        # 获取需要更新的数据（排除未设置的字段）
        tcping_dict = tcping_data.model_dump(exclude_unset=True)
        
        # 更新tcping部分的配置
        config['tcping'] = {**config.get('tcping', {}), **tcping_dict}
        
        # 调用ProviderManager的update_config_by_name方法来更新数据库
        await self.provider_manager.update_config_by_name(provider_id, 'tcping', config['tcping'])
        
        # 获取更新后的Provider对象
        updated_provider = await self.get_provider_by_id(provider_id)
        return updated_provider

    async def update_provider_curl(self, provider_id: int, curl_data: ProviderUpdateCurl) -> Optional[Provider]:
        """更新供应商的Curl设置"""
        current_provider = await self.get_provider_by_id(provider_id)
        if current_provider is None:
            logging.warning(f"Provider with ID {provider_id} not found.")
            return None

        # 获取当前配置
        config = current_provider.config or {}

        # 获取需要更新的数据（排除未设置的字段）
        curl_dict = curl_data.model_dump(exclude_unset=True)

        # 更新curl部分的配置
        config['curl'] = {**config.get('curl', {}), **curl_dict}

        # 调用ProviderManager的update_config_by_name方法来更新数据库
        await self.provider_manager.update_config_by_name(provider_id, 'curl', config['curl'])

        # 获取更新后的Provider对象
        updated_provider = await self.get_provider_by_id(provider_id)
        return updated_provider

    async def update_provider_monitor(self, provider_id: int, monitor_data: ProviderUpdateMonitor) -> Optional[Provider]:
        """更新供应商的监控设置"""
        current_provider = await self.get_provider_by_id(provider_id)
        if current_provider is None:
            return None

        config = current_provider.config or {}
        monitor_dict = monitor_data.model_dump(exclude_unset=True)
        # 在这里进行二次加工
        # 例如：monitor_dict['some_field'] = some_function(monitor_dict['another_field'])
        config['monitor'] = monitor_dict
        updated_provider_data = {'id': provider_id, 'config': json.dumps(config)}
        return await self.update_provider(provider_id, updated_provider_data)

    # async def update_provider_ip_range(self, provider_id: int, ip_range_data: ProviderUpdateIPRange) -> Optional[Provider]:
    #     """更新供应商的IP范围设置（CIDR形式）"""
    #     current_provider = await self.get_provider_by_id(provider_id)
    #     if current_provider is None:
    #         return None

    #     ip_range_dict = ip_range_data.model_dump()
    #     # 在这里进行二次加工
    #     # 例如：ip_range_dict['some_field'] = some_function(ip_range_dict['another_field'])
    #     await self.ip_range_manager.update_ip_range(provider_id, ip_range_dict['cidrs'])
    #     return current_provider

    # async def update_provider_start_ip_end_ip(self, provider_id: int, start_ip_end_ip_data: ProviderUpdateStartIP_EndIP) -> Optional[Provider]:
    #     """更新供应商的IP范围设置（开始IP到结束IP形式）"""
    #     current_provider = await self.get_provider_by_id(provider_id)
    #     if current_provider is None:
    #         return None

    #     start_ip_end_ip_dict = start_ip_end_ip_data.model_dump()
    #     # 在这里进行二次加工
    #     # 例如：start_ip_end_ip_dict['some_field'] = some_function(start_ip_end_ip_dict['another_field'])
    #     await self.ip_range_manager.update_start_ip_end_ip(provider_id, start_ip_end_ip_dict['startip_endip'])
    #     return current_provider

    # async def update_provider_ip(self, provider_id: int, ip_data: ProviderUpdateIP) -> Optional[Provider]:
    #     """更新供应商的单个IP地址"""
    #     current_provider = await self.get_provider_by_id(provider_id)
    #     if current_provider is None:
    #         return None

    #     ip_dict = ip_data.model_dump()
    #     # 在这里进行二次加工
    #     # 例如：ip_dict['some_field'] = some_function(ip_dict['another_field'])
    #     await self.ip_range_manager.update_ip(provider_id, ip_dict['ips'])
    #     return current_provider

    async def delete_provider(self, provider_id: int) -> bool:
        """删除供应商,因为provider和ips和ip_range都有主外键的关系,所以这个功能不可能快.只能让前端等"""
        """或者采用软删除,可以在前端无感删除数据"""
        try:
            await self.provider_manager.delete_provider(provider_id)
            task1 = asyncio.create_task(self.ip_manager.delete_ips_by_provider(provider_id=provider_id))
            task2 = asyncio.create_task(self.ip_range_manager.delete_ip_ranges_by_provider(provider_id))
            return True
        except Exception as e:
            raise e                  
    
    
    async def get_provider_with_ip_ranges(self,provider_id: int):
        try:
            provider = await self.provider_manager.get_provider_by_id(provider_id)
            ip_ranges = await self.ip_range_manager.get_ip_ranges_by_provider_id(provider_id)
            provider.ip_ranges = ip_ranges
            return provider
        except Exception as e:
            raise e
            

    async def delete_ip_ranges_by_provider(self, provider_id: int):
        try:
            return await self.ip_range_manager.delete_ip_ranges_by_provider(provider_id)
        except Exception as e:
            raise e
    
    
    