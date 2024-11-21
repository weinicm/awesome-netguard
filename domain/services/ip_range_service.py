import asyncio
import ipaddress
import logging
from typing import Dict, List, Optional, Tuple
import aiohttp
from domain.managers.ip_range_manager import IPRangeManager
from domain.schemas.ip_range import IPRange, IPRangeSource, IPRangesByProviderResponse, IPRangeCreateFromAPI,IPRangeCreateFromCidrs, IPRangeCreateFromCustomRange,IPRangeCreateFromSingleIps,IPRangeSource
from services.logger import setup_logger
from services.pubsub_service import PubSubService

logger = setup_logger(__name__)

class IPRangeService:
    def __init__(self,ip_range_manager: IPRangeManager,pubsub_service: PubSubService):
        self.ip_range_manager = ip_range_manager
        self.pubsub_service =   pubsub_service

    async def get_ip_ranges(self) -> List[IPRange]:
        return await self.ip_range_manager.get_ip_ranges()

    async def get_ip_range_by_id(self, ip_range_id: int) -> Optional[IPRange]:
        return await self.ip_range_manager.get_ip_range_by_id(ip_range_id)
    
    async def get_ip_ranges_by_provider(self, provider_id: int) -> IPRangesByProviderResponse:
        try:
            ip_ranges = await self.ip_range_manager.get_ip_ranges_by_provider_id(provider_id)
            logger.info(f"我的数据: {ip_ranges}")  # Corrected logging statement
            if ip_ranges is None:
                return IPRangesByProviderResponse(provider_id = provider_id,api_url=[], custom_ranges=[], single_ips=[])
        except Exception as e:
            logger.error(f"Failed to get IP ranges by provider ID: {e}")
            raise e
        
        for ip_rang in ip_ranges:
            logger.info(f"我的数据: {ip_rang.source.value}")    
    
        response_data ={
            "provider_id": provider_id,
            "api_range_list":[ip_range for ip_range in ip_ranges if ip_range.source.value == IPRangeSource.API.value],
            "custom":[ip_range for ip_range in ip_ranges if ip_range.source.value == IPRangeSource.CUSTOM.value],
            "single_ips":[ip_range for ip_range in ip_ranges if ip_range.source.value == IPRangeSource.SINGLE.value],
            "cidrs":[ip_range for ip_range in ip_ranges if ip_range.source.value == IPRangeSource.CIDRS.value]
        }
        return IPRangesByProviderResponse(**response_data)
    
    async def create_from_api(self, create_ip_range_data: IPRangeCreateFromAPI) -> bool:
        """
        从 API 创建 IP 范围

        Args:
            create_ip_range_data (IPRangeCreateFromAPI): 包含 API URL 和提供者 ID 的数据对象

        Returns:
            bool: 创建是否成功
        """

        try:
            ipv4_ranges, ipv6_ranges = await self.fetch_ip_ranges_from_api(create_ip_range_data.api_url)
        except Exception as e:
            raise e

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

            ip_range = {
                "start_ip": start_ip,
                "end_ip": end_ip,
                "provider_id": create_ip_range_data.provider_id,
                
                "source": IPRangeSource.CIDRS.value,
                "cidr": cidr
            }
            ip_ranges.append(ip_range)

        logger.info(f"Creating IP ranges from API: {ip_ranges}")
        try:
            await self.ip_range_manager.delete_ip_range_by_source(create_ip_range_data.provider_id, IPRangeSource.API.value)
            saved_ip_ranges = await self.ip_range_manager.save_ip_ranges(ip_ranges)
            return True
        except Exception as e:
            logger.error(f"Failed to create IP ranges from API: {e}")
            raise e
    
    
    async def update_ip_ranges_from_cidrs(self, ip_range_data: IPRangeCreateFromCidrs) -> List[IPRange]:
        """
        从 CIDR 列表创建 IP 范围

        Args:
            ip_range_data (IPRangeCreateFromCidrs): 包含 CIDR 列表和提供者 ID 的数据对象

        Returns:
            List[IPRange]: 创建的 IP 范围列表
        """
        cidrs = ip_range_data.cidrs

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

            ip_range = {
                "start_ip": start_ip,
                "end_ip": end_ip,
                "provider_id": ip_range_data.provider_id,
                "source": IPRangeSource.CIDRS.value,
                "cidr": cidr
            }
            ip_ranges.append(ip_range)

        logger.info(f"Creating IP ranges from CIDRs: {ip_ranges}")
        try:
            # 保存到数据库并获取生成的 id
            await self.ip_range_manager.delete_ip_range_by_source(ip_range_data.provider_id, IPRangeSource.CIDRS.value)
            saved_ip_ranges = await self.ip_range_manager.save_ip_ranges(ip_ranges)
            return saved_ip_ranges
        except Exception as e:
            logger.error(f"Failed to create IP ranges from CIDRs: {e}")
            raise Exception("Failed to create IP ranges from CIDRs")


    async def update_ip_range_from_single_ips(self, iprange_data: IPRangeCreateFromSingleIps) -> List[Dict]:
        """
        从单个 IP 地址列表创建 IP 范围

        Args:
            iprange_data (IPRangeCreateFromSingleIps): 包含单个 IP 地址列表和提供者 ID 的数据对象

        Returns:
            List[Dict]: 创建的 IP 范围列表
        """
        ips = iprange_data.single_ips

        # 将每个 IP 地址转换为 IP 范围
        ip_ranges = []
        for ip in ips:
            ip_range = {
                "start_ip": ip,
                "end_ip": ip,
                "provider_id": iprange_data.provider_id,
                "source": IPRangeSource.SINGLE.value,
                "cidr": None  # 单个 IP 地址没有 CIDR
            }
            ip_ranges.append(ip_range)

        logger.info(f"Creating IP ranges from single IPs: {ip_ranges}")
        try:
            await self.ip_range_manager.delete_ip_range_by_source(iprange_data.provider_id, IPRangeSource.SINGLE.value)
            return await self.ip_range_manager.save_ip_ranges(ip_ranges)
        except Exception as e:
            logger.error(f"Failed to create IP ranges from single IPs: {e}")
            raise ValueError("Failed to create IP ranges from single IPs")

    
    async def update_ip_range_from_custom_ranges(self, ip_range_data: IPRangeCreateFromCustomRange) -> List[Dict]:
        """
        从自定义 IP 范围列表创建 IP 范围

        Args:
            ip_range_data (IPRangeCreateFromCustomRange): 包含自定义 IP 范围列表和提供者 ID 的数据对象

        Returns:
            List[Dict]: 创建的 IP 范围列表
        """
        custom_ranges = ip_range_data.custom_ranges

        # 将每个自定义范围转换为 IP 范围
        ip_ranges = []
        try:
            for custom_range in custom_ranges:
                ip_range = {
                    "start_ip": custom_range['start_ip'],
                    "end_ip": custom_range['end_ip'],
                    "provider_id": ip_range_data.provider_id,
                    "source": IPRangeSource.CUSTOM.value,
                    "cidr": None  # 自定义范围没有 CIDR
                }
                ip_ranges.append(ip_range)

            logger.info(f"Creating IP ranges from custom ranges: {ip_ranges}")
            try:
                # 只能先删除,再插入了
                await self.ip_range_manager.delete_ip_range_by_source(ip_range_data.provider_id, IPRangeSource.CUSTOM.value)
                return await self.ip_range_manager.save_ip_ranges(ip_ranges)
            except Exception as e:
                logger.error(f"Failed to create IP ranges from custom ranges: {e}")
                raise e
        except Exception as e:
            logger.error(f"Failed to process custom ranges: {e}")
            raise e

    
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
        max_retries = 3
        retry_delay = 5  # 重试间隔时间（秒）
        headers = {
            'Content-Type': 'application/json'
        }
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url,headers=headers) as resp:
                        if resp.status != 200:
                            raise ValueError(f"Failed to fetch data from API: {resp.status}")
                        data = await resp.json()

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
                            logger.info(f"有ipv6: {prefix['ipv6_prefix']}")
                            ipv6_cidrs.append(prefix['ipv6_prefix'])

                    return ipv4_cidrs, ipv6_cidrs

            except aiohttp.ClientError as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise ValueError(f"Failed to fetch data from API after {max_retries} attempts: {e}")
            except ValueError as e:
                logger.error(f"Failed to fetch data from API: {e}")
                raise
            
            
    async def delete_ip_range_by_id(self, ip_range_id: int):
        return await self.ip_range_manager.delete_ip_range_by_id(ip_range_id)
    
    
    # async def delete_ip_range_by_api(self, range_data:IPRangeCreateFromAPI):
    #     return await self.ip_range_manager.delete_ip_range_by_source(range_data.provider_id, IPRangeSource.API.value)