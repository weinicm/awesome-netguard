import logging
from typing import List, Optional
from domain.schemas.test_result import TestResult
from db.db_manager import DBManager

class TestResultManager:
    
    def __init__(self,db_manager:DBManager):
        self.db_manage = db_manager

    # ip不会重复,所以有重复的时候,直接更新. ON CONFLICT (ip) DO UPDATE SET
   
    async def insert_test_result(self, test_result: dict) -> bool:
        try:
            query = """
            INSERT INTO test_results (ip, avg_latency, std_deviation, packet_loss)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (ip) DO UPDATE SET
                avg_latency = EXCLUDED.avg_latency,
                std_deviation = EXCLUDED.std_deviation,
                packet_loss = EXCLUDED.packet_loss;
            """
            values = [
                test_result.get('ip'),
                test_result.get('avg_latency'),
                test_result.get('std_deviation'),
                test_result.get('packet_loss')
            ]
            await self.db_manage.execute(query, *values)
            return True
        except Exception as e:
            logging.error(f"Failed to insert/update test result: {e}")
            return False
    
    async def get_test_results_by_provider(self, provider_id: int) -> Optional[list[TestResult]]:
        query = "SELECT * FROM test_results WHERE provider_id = $1;"
        results = await self.db_manage.fetch(query, provider_id)
        if results:
            return [TestResult.from_record(record) for record in results]
        return None
    
    async def solfy_delete_test_result_by_ip(self, ip: str) -> bool:
        query = "UPDATE test_results SET is_delete = true WHERE ip = $1;"
        try:
            await self.db_manage.execute(query, ip)
            return True
        except Exception as e:
            logging.error(f"Failed to delete test result: {e}")
            return False
        
    async def delete_test_result_by_ip(self, ip: str) -> bool:
        query = "DELETE FROM test_results WHERE ip = $1;"
        try:
            await self.db_manage.execute(query, ip)
            return True
        except Exception as e:
            logging.error(f"Failed to delete test result: {e}")
            return False

    async def update_test_speed(self,ip:str,speed:float):
        query = "UPDATE test_results SET download_speed = $1 WHERE ip = $2;"
        try:
            await self.db_manage.execute(query,speed,ip)
            return True
        except Exception as e:
            logging.error(f"Failed to update test result: {e}")
            return False
        
    async def lock_ip(self,ip:str):
        query = "UPDATE test_results SET is_locked = true WHERE ip = $1;"
        try:
            await self.db_manage.execute(query,ip)
            return True
        except Exception as e:
            logging.error(f"Failed to lock test result: {e}")
            return False
        
    async def unlock_ip(self,ip:str):
        query = "UPDATE test_results SET is_locked = false WHERE ip = $1;"
        try:
            await self.db_manage.execute(query,ip)
            return True
        except Exception as e:
            logging.error(f"Failed to unlock test result: {e}")
            return False
        
    # async def get_better_test_result_ip(self, provider_id: int) -> Optional[list[TestResult]]:
    #     query = "SELECT * FROM test_results WHERE provider_id = $1"
    #     results = await self.db_manage.fetch(query, provider_id)
    #     if results:
    #         return [TestResult.from_record(record) for record in results]
    #     return None
    

    async def get_better_ips(self, count: int = 1) -> Optional[List[TestResult]]:
        query = """
        SELECT * FROM test_results 
        ORDER BY avg_latency ASC, packet_loss DESC 
        LIMIT $1;
        """
        results = await self.db_manage.fetch(query, count)
        if results:
            return [TestResult.from_record(record) for record in results]
        return None
    
    async def delete_invalid_ips_by_curl_config(self):
        query = "DELETE FROM test_results WHERE download_speed = -1"
        await self.db_manage.execute(query)
        
    async def delete_invalid_ips_by_tcping_config(self,max_avg_latency,max_loss_packet):
        query = "DELETE FROM test_results WHERE avg_latency > $1 OR packet_loss > $2"
        try:  
            await self.db_manage.execute(query,max_avg_latency,max_loss_packet)
        except Exception as e:
            raise e
        
    async def has_speed_value(self):
        query = "SELECT * FROM test_results WHERE download_speed is not null and download_speed <> -1"
        results = await self.db_manage.fetch(query)
        if results:
            return True
        return False
    
    async def get_best_ip(self):
       query =" SELECT * FROM public.test_results where download_speed is not null order by std_deviation asc limit 1"
       result = await self.db_manage.fetchrow(query=query)
       if result:
           return TestResult.from_record(result)
       return None    
    