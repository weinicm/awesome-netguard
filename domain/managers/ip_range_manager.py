from typing import Dict, List, Optional
from domain.schemas.ip_range import IPRange  # 假设 IPRange 模型在 domain/models/ip_range.py 文件中定义
from db.db_manager import DBManager
from services.logger import setup_logger

logger = setup_logger(__name__)

class IPRangeManager:
    def __init__(self,db_manager:DBManager):
        self.db_manager = db_manager

    async def get_ip_ranges(self) -> List[IPRange]:
        query = "SELECT * FROM ip_ranges"
        records = await self.db_manager.fetch(query)
        ip_ranges = [IPRange.from_record(record) for record in records]
        return ip_ranges

    
    async def get_ip_range_by_id(self, ip_range_id: int) -> Optional[IPRange]:
        query = "SELECT * FROM ip_ranges WHERE id = $1"
        params = (ip_range_id,)
        record = await self.db_manager.fetchrow(query, params)
        if record:
            return IPRange.from_record(record[0])
        return None

    async def save_ip_ranges(self, ip_ranges: List[Dict]) -> bool:
        query = "INSERT INTO ip_ranges (start_ip, end_ip, provider_id, source, cidr) VALUES ($1, $2, $3, $4, $5)"
        values = [(ip_range["start_ip"], ip_range["end_ip"], ip_range["provider_id"], ip_range["source"], ip_range["cidr"]) for ip_range in ip_ranges]
        try:
            await self.db_manager.execute_many(query, values)
            return True
        except Exception as e:
            logger.error(f"Failed to save IP ranges: {e}")
            return False

    async def delete_ip_range_by_id(self, ip_range_id: int) -> bool:
        query = "DELETE FROM ip_ranges WHERE id = $1"
        params = (ip_range_id,)
        try:
            await self.db_manager.execute(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to delete IP range: {e}")
            return False
        
    async def get_ip_ranges_by_provider_id(self, provider_id: int) -> List[IPRange]:
        query = "SELECT * FROM ip_ranges WHERE provider_id = $1"
        params = (provider_id,)
        records = await self.db_manager.fetch(query, params)
        ip_ranges = [IPRange.from_record(record) for record in records]
        return ip_ranges
    
    async def delete_ip_range_by_source(self, provider_id: int, source: str) -> bool:       
        query = "DELETE FROM ip_ranges WHERE provider_id = $1 AND source = $2"
        params = (provider_id, source)
        try:
            await self.db_manager.execute(query, *params)
            return True
        except Exception as e:
            logger.error(f"Failed to delete IP range: {e}")
            return False