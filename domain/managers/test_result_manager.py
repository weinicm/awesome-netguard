import logging
from typing import Optional
from domain.schemas.test_result import TestResult
from db.db_manager import DBManager

class TestResultManager:
    
    def __init__(self,db_manage:DBManager):
        self.db_manage = db_manage

    # ip不会重复,所以有重复的时候,直接更新. ON CONFLICT (ip) DO UPDATE SET
    async def insert_test_result(self, test_result: dict) -> bool:
        query = """
        INSERT INTO test_results (ip, avg_latency, std_deviation, packet_loss, download_speed, is_locked, status, test_type, is_delete)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (ip) DO UPDATE SET
            avg_latency = EXCLUDED.avg_latency,
            std_deviation = EXCLUDED.std_deviation,
            packet_loss = EXCLUDED.packet_loss,
            download_speed = EXCLUDED.download_speed,
            is_locked = EXCLUDED.is_locked,
            status = EXCLUDED.status,
            test_type = EXCLUDED.test_type,
            is_delete = EXCLUDED.is_delete;
        """
        values = [
            test_result.get('ip'),
            test_result.get('avg_latency'),
            test_result.get('std_deviation'),
            test_result.get('packet_loss'),
            test_result.get('download_speed'),
            test_result.get('is_locked'),
            test_result.get('status'),
            test_result.get('test_type'),
            test_result.get('is_delete')
        ]
        try:
            await self.db_manage.execute(query, *values)
            return True
        except Exception as e:
            logging.error(f"Failed to insert/update test result: {e}")
            return False
    
    async def get_test_results_by_provider(self, provider_id: int) -> Optional[list[TestResult]]:
        query = "SELECT * FROM test_result WHERE provider_id = $1;"
        results = await self.db_manage.fetch(query, provider_id)
        if results:
            return [TestResult.from_record(record) for record in results]
        return None
    
    async def solfy_delete_test_result_by_ip(self, ip: str) -> bool:
        query = "UPDATE test_result SET is_delete = true WHERE ip = $1;"
        try:
            await self.db_manage.execute(query, ip)
            return True
        except Exception as e:
            logging.error(f"Failed to delete test result: {e}")
            return False
        
    async def delete_test_result_by_ip(self, ip: str) -> bool:
        query = "DELETE FROM test_result WHERE ip = $1;"
        try:
            await self.db_manage.execute(query, ip)
            return True
        except Exception as e:
            logging.error(f"Failed to delete test result: {e}")
            return False

    async def update_test_speed(self,provider_id:int,ip:str,speed:float):
        query = "UPDATE test_result SET download_speed = $1 WHERE provider_id = $2 AND ip = $3;"
        try:
            await self.db_manage.execute(query,speed,provider_id,ip)
            return True
        except Exception as e:
            logging.error(f"Failed to update test result: {e}")
            return False
        
    async def lock_ip(self,ip:str):
        query = "UPDATE test_result SET is_locked = true WHERE ip = $1;"
        try:
            await self.db_manage.execute(query,ip)
            return True
        except Exception as e:
            logging.error(f"Failed to lock test result: {e}")
            return False
        
    async def unlock_ip(self,ip:str):
        query = "UPDATE test_result SET is_locked = false WHERE ip = $1;"
        try:
            await self.db_manage.execute(query,ip)
            return True
        except Exception as e:
            logging.error(f"Failed to unlock test result: {e}")
            return False
        
    async def get_better_test_result_ip(self, provider_id: int) -> Optional[list[TestResult]]:
        query = "SELECT * FROM test_result WHERE provider_id = $1"
        results = await self.db_manage.fetch(query, provider_id)
        if results:
            return [TestResult.from_record(record) for record in results]
        return None
    

