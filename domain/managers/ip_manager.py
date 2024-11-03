import logging
from typing import Any, Dict, List, Optional
from domain.models.provider import Provider  # 假设 Provider 模型在 domain/models/provider.py 文件中定义
from db.dbmanager import DBManager
from domain.models.ip_address import IPAddress

class IpaddressManager:
    def __init__(self):
        self.db_manager = DBManager()

    async def get_ips_by_provider(self, provider_id: int, ip_type: str, count: int, randomize: bool = False) -> List[IPAddress]:
        """从数据库中获取指定提供商的IP地址"""
        
        if randomize:
            # 使用 ORDER BY RANDOM() 进行随机抽样
            query = """
                SELECT ip_address, ip_type
                FROM ips
                WHERE provider_id = $1 AND ip_type = $2
                ORDER BY RANDOM()
                LIMIT $3
            """
        else:
            query = """
                SELECT ip_address, ip_type
                FROM ips
                WHERE provider_id = $1 AND ip_type = $2
                LIMIT $3
            """

        try:
            logging.debug(f"Executing query: {query} with args: {provider_id, ip_type, count}")
            result = await self.db_manager.fetch(query, provider_id, ip_type, count)
            return [IPAddress(ip_address=row['ip_address'], ip_type=row['ip_type'], provider_id=provider_id) for row in result]
        except Exception as e:
            logging.error(f"Error executing fetch: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Args: {provider_id, ip_type, count}")
            # 处理异常，例如返回一个空列表或默认值
            return []
        

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