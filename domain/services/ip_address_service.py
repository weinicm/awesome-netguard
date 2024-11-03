import asyncio
import ipaddress
import json
import logging
import random
from typing import Any, Dict, List

from domain.managers.ip_range_manager import IPRangeManager
from domain.managers.provider_manager import ProviderManager
from domain.managers.ip_manager import IpaddressManager  # 假设 IPManager 在 domain/managers/ip_manager.py 文件中定义
from domain.models.ip_address import IPAddress
from domain.services import queue_service
from domain.services.pubsub_service import PubSubService
from domain.models.ip_range import IPRange

class IPAddressService:
    def __init__(self):
        self.ip_manager = IpaddressManager()
        self.ip_range_manager = IPRangeManager()
        self.provider_manager = ProviderManager()
        self.semaphore = asyncio.Semaphore(1)  # 插入ip时限制并发数为10
        self.queue_service = queue_service
        self.pubsub_service = PubSubService()

    
    async def store_provider_ips(self, provider_id: int):
        try:
            # 获取IP范围
            ip_ranges = await self.ip_range_manager.get_ip_ranges_by_provider_id(provider_id)
            if not ip_ranges:
                logging.info(f"No IP ranges found for provider {provider_id}")
                return
            logging.info(f"Found {len(ip_ranges)} IP ranges for provider {provider_id}")

            # 删除旧的IP范围
            await self.ip_manager.delete_ips_by_provider(provider_id)

            # 初始化 all_items 列表
            all_items = []
            for ip_range in ip_ranges:
                all_items.extend(self.convert_ip_range_to_ips(ip_range))

            # 总的 IP 数量
            total_items = len(all_items)

            # 初始化已处理的 IP 数量
            processed_items = 0

            # 分批处理数据
            batch_size = 2000  # 每次从总数据中取出的批次大小

            # 限制并发任务数量为5
            semaphore = asyncio.Semaphore(10)

            # 分批处理数据
            async def process_batch(batch):
                nonlocal processed_items
                async with semaphore:
                    # 批量插入数据库
                    success = await self.ip_manager.batch_insert_ips(batch)
                    if not success:
                        logging.error(f"Failed to insert batch of IPs")
                        return 0
                    processed_count = len(batch)
                    processed_items += processed_count

                    # 更新进度
                    progress_data = {
                        "status": "inserting",
                        "progress": round(processed_items / total_items, 2),
                        "total": total_items,
                        "processed": processed_items,
                        "message": "正在更新IP数据"
                    }

                    # 发布进度更新
                    try:
                        await self.pubsub_service.publish("progress_updates", json.dumps(progress_data))
                    except Exception as e:
                        logging.error(f"Failed to publish progress update. Error: {e}")

                    return processed_count

            # 创建并发任务列表
            tasks = []
            for i in range(0, len(all_items), batch_size):
                batch = all_items[i:i + batch_size]
                task = asyncio.create_task(process_batch(batch))
                tasks.append(task)

            # 等待所有任务完成
            await asyncio.gather(*tasks)

            logging.info("All IP data processing completed.")

        except Exception as e:
            logging.error(f"Failed to get and process IP ranges for provider {provider_id}. Error: {e}")
            raise
        

    async def insert_batch_task(self, batch: List[Dict[str, str]], processed_items: int, total_items: int):
        """ 异步插入一批 IP 地址 """
        # 批量插入数据库
        await self.ip_manager.batch_insert_ips(batch)
        
        # 更新已处理的 IP 数量
        processed_items += len(batch)
        
    async def delete_ips_by_provider(self, provider_id: int) -> bool:
        return await self.ip_range_manager.delete_ip_ranges_by_provider(provider_id)
    

    def convert_ip_range_to_ips(self, ip_range: IPRange) -> List[Dict[str, str]]:
        """将单个 IP 范围转换为带有 IP 类型和 provider_id 的 IP 地址列表"""
        ip_list = []
        
        start_ip = ipaddress.ip_address(ip_range.start_ip)
        end_ip = ipaddress.ip_address(ip_range.end_ip)
        provider_id = ip_range.provider_id
        
        # 确定 IP 类型
        ip_type = 'IPv4' if isinstance(start_ip, ipaddress.IPv4Address) else 'IPv6'
        
        # 生成 IP 列表
        if ip_type == 'IPv4':
            for ip_int in range(int(start_ip), int(end_ip) + 1):
                ip_str = str(ipaddress.ip_address(ip_int))
                ip_list.append({
                    'ip_address': ip_str,
                    'ip_type': ip_type,
                    'provider_id': provider_id
                })
        elif ip_type == 'IPv6':
            total_ips = int(end_ip) - int(start_ip) + 1
            if total_ips > 500000:
                # IPv6 数据量过大，从每一个段上随机选择 50 万个 IP 地址
                random_ips = [random.randint(int(start_ip), int(end_ip)) for _ in range(500000)]
                for ip_int in random_ips:
                    ip_str = str(ipaddress.ip_address(ip_int))
                    ip_list.append({
                        'ip_address': ip_str,
                        'ip_type': ip_type,
                        'provider_id': provider_id
                    })
            else:
                # 如果总数小于 50 万，则生成全部 IP 地址
                for ip_int in range(int(start_ip), int(end_ip) + 1):
                    ip_str = str(ipaddress.ip_address(ip_int))
                    ip_list.append({
                        'ip_address': ip_str,
                        'ip_type': ip_type,
                        'provider_id': provider_id
                    })

        return ip_list
    
    async def get_ips_by_provider(self, provider_id: int, ip_type: str, count: int, randomize: bool = False) -> List[IPAddress]:
        return await self.ip_manager.get_ips_by_provider(provider_id, ip_type, count, randomize)
    

    async def get_ipsv4_by_provider(self, provider_id: int, count: int, randomize: bool = True) -> List[str]:
        return await self.get_ips_by_provider(provider_id, 'IPv4', count, randomize)
    
    async def get_ipsv6_by_provider(self, provider_id: int, count: int, randomize: bool = True) -> List[str]:
        return await self.get_ips_by_provider(provider_id, 'IPv6', count, randomize)    