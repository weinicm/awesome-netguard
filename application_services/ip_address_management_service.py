import ipaddress
import logging
import random
from typing import List
import aiohttp
from ipaddress import ip_network,IPv4Network
from schemas1 import IPRangeInput  # 假设 IPRangeInput 模型在 schemas.py 文件中定义
from domain.services.config_service import ConfigService
from domain.services.ip_address_service import IPAddressService
from domain.services.provider_service import ProviderService
from domain.services.ip_range_service import IPRangeService

class IPAddressManagementService:
    def __init__(self, provider_id: int):
        self.config_service = ConfigService()
        self.ipaddr_service = IPAddressService()  # 请确保 db_manager 已经初始化
        self.provider_service = ProviderService()
        self.ip_range_service = IPRangeService()
        self.provider = None
        self.provider_id = None
        self.provider_name = None
        self.default_v4_count = None
        self.default_v6_count = None
        self.return_count_ips = None

        # 异步初始化
        self._initialize(provider_id)

    async def _initialize(self, provider_id: int):
        self.provider = await self.provider_service.get_provider_by_id(provider_id)
        if self.provider:
            self.provider_id = self.provider.get('id')
            self.provider_name = self.provider.get('name')
        else:
            raise ValueError(f"Provider with ID {provider_id} not found")

        self.default_v4_count = self.config_service.get_config('ipv4_count', default=None)  # None means all
        self.default_v6_count = self.config_service.get_config('ipv6_count', default=300000)
        self.return_count_ips = self.config_service.get_system_config('return_count_ips', default=100)

    # 从api获取ip_range
    async def fetch_data_from_api(self,provider_name,api_url):
        # 获取provider信息
        if not provider_name:
            raise ValueError("Provider name not found")

        if not api_url:
            raise ValueError("Provider API URL not found")

        # 使用aiohttp异步请求API
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch data from API: {response.status}")
                
                data = await response.json()

                # 根据不同的provider名称处理数据
                if provider_name == 'cloudflare':
                    if not data.get('success'):
                        raise ValueError("API request failed for cloudflare")
                    
                    result = data.get('result', {})
                    ipv4_cidrs = result.get('ipv4_cidrs', [])
                    ipv6_cidrs = result.get('ipv6_cidrs', [])

                    return 'cidrs', ipv4_cidrs + ipv6_cidrs  # 合并IPv4和IPv6的CIDR列表
                else:
                    raise ValueError("Unsupported provider name")
    # ip_range 格式化 统一为: start_ip,end_ip
    def parse_ip_ranges(self, data_format: str, data: List):
        ip_ranges = []
        if data_format == 'cidrs':
            for cidr in data:
                network = ip_network(cidr)
                ip_type = 'IPv4' if isinstance(network, IPv4Network) else 'IPv6'
                ip_ranges.append({
                    'cidr': cidr,  # 保留原始的CIDR字段
                    'start_ip': str(network.network_address),
                    'end_ip': str(network.broadcast_address),
                    'provider_id': self.provider_id,
                    'provider_name': self.provider_name,
                    'ip_type': ip_type
                })
        elif data_format == 'startip_endip':
            for item in data:
                start_ip = item.start_ip
                end_ip = item.end_ip
                if not start_ip or not end_ip:
                    raise ValueError("Invalid startip_endip format")
                ip_type = 'IPv4' if ':' not in start_ip else 'IPv6'
                ip_ranges.append({
                    'start_ip': start_ip,
                    'end_ip': end_ip,
                    'provider_id': self.provider_id,
                    'provider_name': self.provider_name,
                    'ip_type': ip_type
                })
        elif data_format == 'single_ips':
            for ip in data:
                ip_type = 'IPv4' if ':' not in ip else 'IPv6'
                ip_ranges.append({
                    'start_ip': ip,
                    'end_ip': ip,
                    'provider_id': self.provider_id,
                    'provider_name': self.provider_name,
                    'ip_type': ip_type
                })

        return ip_ranges

    # 存存储ip_range
    async def create_ip_range(self, data: dict):
        # 存储处理后的IP范围数据
        return await self.ip_range_service.create_ip_range(data)

 
    # 返回指定供应商的ip
    async def get_all_ip_ranges(self):
        provider_id =self.provider_id
        """
        获取指定供应商的所有 IP 范围
        """
        records = await self.ip_range_service.get_ip_ranges_by_provider_id(provider_id)
        ip_ranges = []
        for record in records:
            ip_range = {
                'id': record['id'],
                'start_ip': record['start_ip'],
                'end_ip': record['end_ip'],
                'provider_id': record['provider_id']
            }
            ip_ranges.append(ip_range)
        return ip_ranges

    async def get_ips_v4_by_provider(self, count=None):
        provider_id  = self.provider_id
        ip_type = 'v4'
        if count is None:
            count = self.return_count_ips
        await self.ipaddr_service.get_ips_by_provider(provider_id, ip_type,count)

    async def get_ips_v6_by_provider(self, count=None):
        provider_id  = self.provider_id
        ip_type = 'v6'
        if count is None:
            count = self.return_count_ips
        await self.ipaddr_service.get_ips_by_provider(provider_id, ip_type,count)

     # 将ip_range 转换为ip,并保存存到数据库中
    async def convert_ip_range_to_ips_and_store(self, start_ip, end_ip, v4_count=None, v6_count=None):
        """
        Save IP range to the database, excluding unusable IPs like broadcast addresses.
        For IPv6, randomly select a specified number of IPs to save.

        Args:
            start_ip (str): Start IP address of the range.
            end_ip (str): End IP address of the range.
            provider (str): Provider name.
            v4_count (int, optional): Maximum number of IPv4 addresses to save. Defaults to None (all).
            v6_count (int, optional): Maximum number of IPv6 addresses to save. Defaults to 100000.

        Returns:
            None
        """
        provider_id = self.provider_id
        # Use default values if not provided
        v4_count = v4_count if v4_count is not None else self.default_v4_count
        v6_count = v6_count if v6_count is not None else self.default_v6_count

        # Determine IP type based on the start_ip
        ip_type = 'v4' if ipaddress.ip_address(start_ip).version == 4 else 'v6'
        max_count = v4_count if ip_type == 'v4' else v6_count

        # Generate IP range
        start = ipaddress.ip_address(start_ip)
        end = ipaddress.ip_address(end_ip)
        ip_range = [ip for ip in ipaddress.IPv6Network(f"{start}/{end}", strict=False) if not ip.is_multicast and not ip.is_reserved and not ip.is_broadcast]

        # Randomly select IPs if it's IPv6
        if ip_type == 'v6':
            ip_range = random.sample(ip_range, min(max_count, len(ip_range)))

        # Batch size for inserting into the database
        batch_size = 1000

        # Save selected IPs to the database in batches
        for i in range(0, len(ip_range), batch_size):
            batch = ip_range[i:i + batch_size]
            ip_data_list = [{'ip_address': str(ip), 'ip_type': ip_type, 'provider_id': provider_id} for ip in batch]
            await self.ipaddr_service.create_ips(ip_data_list)



    """
    #，这个方法需要修改。因为ipRangeinput中的ip_range是一个数组。
    对外提供的接口，用来初始化ip_range数据
    存储IP范围数据，可以是从API获取的数据，也可以是手动输入的数据。
    """
    async def store_ip_ranges(self, data: IPRangeInput = None):
        try:
            if data is None:
                raise ValueError("data cannot be None. provider_id is required.")

            if data.provider_id and not data.data_format and not data.cidrs and not data.startip_endip and not data.single_ips:
                # 从API获取数据
                data_format, fetched_data = await self.fetch_data_from_api()
            else:
                # 处理传入的IPRangeInput模型
                if not data.data_format:
                    raise ValueError("data_format is required when providing data")
                data_dict = data.model_dump()
                data_format = data_dict['data_format']
                fetched_data = (
                    data_dict['cidrs'] if data_format == 'cidrs' else
                    data_dict['startip_endip'] if data_format == 'startip_endip' else
                    data_dict['single_ips']
                )

            processed_data = self.parse_ip_ranges(data_format, fetched_data)
            for ip_range in processed_data:
                await self.create_ip_range(ip_range)

            logging.info("IP ranges stored successfully")
            return {"message": "IP ranges stored successfully"}
        except Exception as e:
            logging.error(f"Failed to store IP ranges: {str(e)}")
            raise Exception(f"ip_range_service: Failed to store IP ranges: {str(e)}")
