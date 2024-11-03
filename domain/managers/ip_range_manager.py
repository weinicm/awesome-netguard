from ast import Dict
import ipaddress
import logging
from typing import List, Optional
from domain.models.ip_range import IPRange  # 假设 IPRange 模型在 domain/models/ip_range.py 文件中定义
from db.dbmanager import DBManager

class IPRangeManager:
    def __init__(self):
        self.db_manager = DBManager()

    async def get_ip_ranges(self) -> List[IPRange]:
        query = "SELECT * FROM ip_ranges;"
        results = await self.db_manager.fetch(query)
        return [IPRange.from_record(result) for result in results]

    async def get_ip_range_by_id(self, ip_range_id: int) -> Optional[IPRange]:
        query = "SELECT * FROM ip_ranges WHERE id = $1;"
        result = await self.db_manager.fetch(query, ip_range_id)
        if result:
            return IPRange.from_record(result[0])
        return None
    async def update_ipranges(self, ip_range_data: dict) -> None:
        """更新指定 ID 的 IP 范围"""
        try:
            provider_id = ip_range_data.get('provider_id')
            ip_ranges = ip_range_data.get('ip_ranges', [])
            range_type = ip_range_data.get('type')

            if not provider_id:
                raise ValueError("提供商 ID 不能为空")
            if not range_type:
                raise ValueError("范围类型不能为空")

            # 如果 ip_ranges 为空，则只执行删除操作
            if not ip_ranges:
                logging.info(f'没有 IP 范围数据，仅删除提供商 {provider_id} 的现有数据')
                await self.delete_ip_ranges_by_provider(provider_id)
                return

            # 插入新记录
            insert_query = """
                INSERT INTO ip_ranges (provider_id, type, cidr, start_ip, end_ip)
                VALUES ($1, $2, $3, $4, $5);
            """

            for ip_range in ip_ranges:
                cidr = ip_range.get('cidr')
                start_ip = ip_range.get('start_ip')
                end_ip = ip_range.get('end_ip')

                if not all([start_ip, end_ip]):
                    logging.warning(f"跳过不完整的 IP 范围: {ip_range}")
                    continue

                logging.info(f"正在插入 IP 范围: provider_id={provider_id}, type={range_type}, cidr={cidr}, start_ip={start_ip}, end_ip={end_ip}")

                # 执行插入操作
                await self.db_manager.execute(insert_query, provider_id, range_type, cidr, start_ip, end_ip)

            logging.info(f"成功更新提供商 {provider_id} 的 IP 范围")

        except Exception as e:
            logging.error(f"更新 IP 范围时发生错误: {e}", exc_info=True)
            raise Exception(f"更新 IP 范围时发生错误: {e}")
    async def create_ip_range(self, ip_range_data: Dict) -> None:
        """创建新的 IP 范围"""
        # 提取数据
        cidr = ip_range_data.get('cidr')
        start_ip = ip_range_data['start_ip']
        end_ip = ip_range_data['end_ip']
        provider_id = ip_range_data['provider_id']

        # SQL 插入语句
        query = """
            INSERT INTO ip_ranges (cidr, start_ip, end_ip, provider_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id, cidr, start_ip, end_ip, provider_id, created_at, updated_at;
        """

        # 执行插入并返回新创建的记录
        try:
            result = await self.db_manager.execute(query, cidr, start_ip, end_ip, provider_id, fetch=True)
        except Exception as e:
            print(f"Error creating IP range: {e}")
        if not result:
            raise ValueError("Failed to create IP range or retrieve the new record")

    async def delete_ip_range(self, ip_range_id: int) -> bool:
        query = "DELETE FROM ip_ranges WHERE id = $1 RETURNING id;"
        result = await self.db_manager.fetch(query, ip_range_id)
        return bool(result)
    
    async def delete_ip_ranges_by_provider(self, provider_id: int) -> bool:
        query = "DELETE FROM ip_ranges WHERE provider_id = $1;"
        try:
            # 执行删除操作
            await self.db_manager.execute(query, provider_id)
            return True
        except Exception as e:
            # 捕获并记录异常
            print(f"Failed to delete IP ranges for provider {provider_id}: {e}")
            return False

    
    async def get_ip_ranges_by_provider_id(self, provider_id: int) -> List[IPRange]:
        """
        获取指定供应商的所有 IP 范围
        """
        if provider_id is None:
            raise ValueError("Provider ID cannot be None")

        query = "SELECT * FROM ip_ranges WHERE provider_id = $1;"
        try:
            results = await self.db_manager.fetch(query, provider_id)
            if results is None:
                logging.warning(f"No results found for provider ID {provider_id}")
                return []
            return [IPRange.from_record(result) for result in results]
        except Exception as e:
            logging.error(f"Error fetching IP ranges for provider {provider_id}: {e}")
            raise
    