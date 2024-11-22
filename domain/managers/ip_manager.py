import logging
from typing import Any, Dict, List, Optional
from db.db_manager import DBManager
from domain.schemas.ipaddress import IPAddress
from domain.schemas.test_result import TestResult

class IpaddressManager:
    def __init__(self,db_manager:DBManager):
        self.db_manager = db_manager

    async def get_better_ips(self,count: int = 1) -> List[TestResult]:
        query = "SELECT * FROM test_results ORDER BY avg_latency ASC, packet_loss Desc LIMIT $1"
        results = await self.db_manager.execute(query,count)
        if results:
             return [TestResult.from_record(record) for record in results]
        return None
   
    async def batch_insert_ips(self, ip_data_list: List[Dict[str, Any]]) -> bool:
        """批量插入IP地址记录"""
        if not ip_data_list:
            return False

        # 获取列名
        columns = ', '.join(ip_data_list[0].keys())

        # 构建占位符
        placeholders = ', '.join([f"({', '.join(['$' + str(i + 1) for i in range(len(ip_data_list[0]))])})"])

        # 构建插入语句
        query = f"""
            INSERT INTO ips ({columns})
            VALUES {placeholders}
        """

        # 提取所有值
        all_values = [tuple(ip_data.values()) for ip_data in ip_data_list]

        try:
            await self.db_manager.execute_many(query, all_values)  # 传递 all_values 列表
            return True
        except Exception as e:
            print(f"Error during batch insert: {e}")
            return False
        
    async def delete_ips_by_provider(self, provider_id: int) -> bool:
        """删除指定提供商的所有IP地址"""
        query = """
            DELETE FROM ips
            WHERE provider_id = $1
        """
        try:
            await self.db_manager.execute(query, provider_id)
            return True
        except Exception as e:
            print(f"Error during delete: {e}")
            
    async def get_ips_by_provider(self, provider_id: int, ip_type: str, count: int = 1, randomize: bool = False) -> List[IPAddress]:
        if randomize:
            query = f"SELECT * FROM ips WHERE provider_id = $1 AND ip_type = $2 ORDER BY RANDOM() LIMIT $3"
        else:
            query = f"SELECT * FROM ips WHERE provider_id = $1 AND ip_type = $2 LIMIT $3"
        
        results = await self.db_manager.fetch(query, provider_id, ip_type, count)
        if results:
            return [IPAddress.from_record(record) for record in results]
        return None