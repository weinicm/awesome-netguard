import ipaddress
import logging
from typing import Dict, List, Optional, Tuple

import aiohttp
from domain.managers.ip_range_manager import IPRangeManager
from domain.models.ip_range import IPRange  # 假设 IPRange 模型在 domain/models/ip_range.py 文件中定义
from schemas.ip_range import IPRangeUpdateAPi, IPRangeUpdateCidrs, IPRangeUpdateCustomRange, IPRangeUpdateIps

class IPRangeService:
    def __init__(self):
        self.ip_range_manager = IPRangeManager()

    async def get_ip_ranges(self) -> List[IPRange]:
        return await self.ip_range_manager.get_ip_ranges()

    async def get_ip_range_by_id(self, ip_range_id: int) -> Optional[IPRange]:
        return await self.ip_range_manager.get_ip_range_by_id(ip_range_id)
    
    async def update_ip_ranges_from_api(self,provider_id: int, api_url: str) -> bool:
        """
        更新 IP 范围从 API

        Args:
            ip_range_data (IPRangeUpdateAPi): 包含 API URL 和提供者 ID 的数据对象

        Returns:
            bool: 更新是否成功
        """
        ipv4_ranges, ipv6_ranges = await self.fetch_ip_ranges_from_api(api_url)

        # 合并 IPv4 和 IPv6 的 CIDR 范围
        cidrs = ipv4_ranges + ipv6_ranges

        # 计算每个 CIDR 的 start_ip 和 end_ip
        ip_ranges = []
        for cidr in cidrs:
            interface = ipaddress.ip_interface(cidr)
            network = interface.network
            if str(interface.ip) == str(network.network_address):
                # 用户输入的是网络地址
                start_ip = str(network.network_address)
                end_ip = str(network.broadcast_address)
            else:
                # 用户输入的是具体的 IP 地址
                start_ip = str(interface.ip)
                end_ip = str(interface.ip)

            ip_ranges.append({
                'cidr': cidr,
                'start_ip': start_ip,
                'end_ip': end_ip
            })

        insert_data = {
            'provider_id': provider_id,
            'ip_ranges': ip_ranges,
            'type': 'api'
        }
        logging.info(f"Updating IP ranges from API: {insert_data}")
        try:
            await self.ip_range_manager.update_ipranges(insert_data)
            return True
        except Exception as e:
            logging.error(f"Failed to update IP ranges from API: {e}")
            return False

    async def update_ip_ranges(self, ip_range_data: IPRangeUpdateCidrs) -> Optional[IPRange]:
        """更新 IP 范围"""
        # 读取 ip_range_data
        cidrs = ip_range_data.cidrs
        type = 'cidr'

        # 计算每个 CIDR 的 start_ip 和 end_ip
        ip_ranges = []
        for cidr in cidrs:
            interface = ipaddress.ip_interface(cidr)
            network = interface.network
            if str(interface.ip) == str(network.network_address):
                # 用户输入的是网络地址
                start_ip = str(network.network_address)
                end_ip = str(network.broadcast_address)
            else:
                # 用户输入的是具体的 IP 地址
                start_ip = str(interface.ip)
                end_ip = str(interface.ip)

            ip_ranges.append({
                'cidr': cidr,
                'start_ip': start_ip,
                'end_ip': end_ip
            })

        # 组合成一个字典
        update_data = {
            'provider_id': ip_range_data.provider_id,
            'ip_ranges': ip_ranges,
            'type':type
        }

        # 调用 ip_range_manager 的 update 方法执行更新
        return await self.ip_range_manager.update_ipranges(update_data)

    async def update_single_ips(self, iprange_data:IPRangeUpdateIps) -> Optional[IPRange]:
        """更新指定 ID 的 IP 地址范围"""
        type = "single_ip"
        ips = iprange_data.single_ips
        # 将每个 IP 地址转换为 IP 范围
        ip_ranges = []
        for ip in ips:
            ip_ranges.append({
                'cidr': None,  # 单个 IP 地址没有 CIDR
                'start_ip': ip,
                'end_ip': ip
            })
        # 组合成一个字典
        update_data = {
            'provider_id': iprange_data.provider_id,
            'ip_ranges': ip_ranges,
            'type': type
        }
        logging.debug(f"Updating single IP ranges: {update_data}")

        # 调用 ip_range_manager 的 update 方法执行更新
        return await self.ip_range_manager.update_ipranges(update_data)

    
    async def update_custom_ranges(self, ip_range_data: IPRangeUpdateCustomRange) -> Optional[IPRange]:
        """更新指定 ID 的自定义 IP 范围"""
        custom_ranges = ip_range_data.custom_ranges
        type = "custom-range"
        # 将每个自定义范围转换为 IP 范围
        ip_ranges = []
        try:
            for custom_range in custom_ranges:
                ip_ranges.append({
                    'cidr': None,  # 自定义范围没有 CIDR
                    'start_ip': custom_range['start_ip'],
                    'end_ip': custom_range['end_ip']
                })

            # 组合成一个字典
            update_data = {
                'provider_id': ip_range_data.provider_id,
                'ip_ranges': ip_ranges,
                'type': type
            }

            # 调用 ip_range_manager 的 update 方法执行更新
            reuslt = await self.ip_range_manager.update_ipranges(update_data)
            return reuslt
        except Exception as e:
            logging.error(f"Failed to update custom ranges: {e}")
        

    async def get_ip_ranges_by_provider_id(self, provider_id: int) -> List[IPRange]:
        """根据提供商 ID 获取 IP 范围列表"""
        return await self.ip_range_manager.get_ip_ranges_by_provider_id(provider_id)
    
    async def fetch_ip_ranges_from_api(self, url: str) -> Tuple[List[str], List[str]]:
        """
        通过 API 获取 IP 范围

        Args:
            url (str): API 的 URL

        Returns:
            Tuple[List[str], List[str]]: A tuple containing two lists, one for IPv4 CIDRs and one for IPv6 CIDRs.

        Raises:
            ValueError: 如果 API 请求失败或不支持的提供商名称
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Failed to fetch data from API: {resp.status}")
                    data = await resp.json()
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to fetch data from API: {e}") from e

        # 判断 URL 是否包含 cloudflare
        if 'cloudflare' in url:
            if not data.get('success'):
                raise ValueError("API request failed for Cloudflare")
            result = data.get('result', {})
            ipv4_cidrs = result.get('ipv4_cidrs', [])
            ipv6_cidrs = result.get('ipv6_cidrs', [])
            return ipv4_cidrs, ipv6_cidrs

        # 检查 URL 是否包含 'cloudfront' 或 'amazonaws'
        if 'cloudfront' in url or 'amazonaws' in url:
        # 符合下面两种情况的的话,就是cdn
        #"region": "GLOBAL",
        #"service": "CLOUDFRONT"
            filtered_prefixes = []
            for prefix in data.get('prefixes', []):

                region = prefix.get('region')
                service = prefix.get('service')
                if region == 'GLOBAL' and service == 'CLOUDFRONT':
                    filtered_prefixes.append(prefix)
            # 提取 IPv4 和 IPv6 CIDR 前缀
            ipv4_cidrs = []
            ipv6_cidrs = []

            for prefix in filtered_prefixes:
                if 'ip_prefix' in prefix:
                    ipv4_cidrs.append(prefix['ip_prefix'])
                if 'ipv6_prefix' in prefix:
                    logging.info(f"有ipv6: {prefix['ipv6_prefix']}")
                    ipv6_cidrs.append(prefix['ipv6_prefix'])

            return ipv4_cidrs, ipv6_cidrs
    
