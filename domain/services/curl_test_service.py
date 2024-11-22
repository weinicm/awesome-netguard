from typing import List
from domain.managers.test_result_manager import TestResultManager
from domain.services.config_service import ConfigService
from services.enqueue_service import EnqueueService
from domain.schemas.config import CurlConfig
from utils.curl import CurlRunner
from services.logger import setup_logger
logger = setup_logger(__name__)


class CurlTestService:
    def __init__(self,test_result_manager: TestResultManager):
        self.test_result_manager = test_result_manager
        
    
    def set_tcping_config(self, curl_config: CurlConfig):
        self.curl_config = curl_config
        
    
    async def run_curl_test(self, ips: List[str] = None):
        """
        Run the curl test asynchronously by pushing the task to the queue.

        Args:
            ip_type (str): The type of IP to test (ipv4 or ipv6).
            provider_id (int): The ID of the provider.
            user_submitted_ips (List[str], optional): A list of user-submitted IPs. Defaults to None.
        """
        if self.curl_config is None:
            raise Exception("CurlConfig not set. Please set it before running curl test.")
        if self.curl_config.download_url =='' or self.curl_config.download_url == None:
            logger.info(f"run curl test error, download_url is empty")
            return
        # Create a curl test task
        for ip in ips:
            result = await CurlRunner.run(ip, self.curl_config.download_url, self.curl_config.port, self.curl_config.time_out)
            if result is None:
                continue
            ip,speed =  result
            if self.curl_config.speed > speed:
                speed = -1  
            await self.test_result_manager.update_test_speed(ip=ip,speed=speed)
    
    async def has_speed_value(self):
        return await self.test_result_manager.has_speed_value()
    
    
    async def delete_invalid_ips_by_curl_option(self):
        await self.test_result_manager.delete_invalid_ips_by_curl_config()
    