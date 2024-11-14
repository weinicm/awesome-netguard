from datetime import datetime
import logging
from typing import List, Dict, Any, Tuple
from uuid import uuid4
from domain.schemas.test_result import BatchTestRequest
from services.pubsub_service import PubSubService
from services.cache import CacheService
from domain.services.ip_address_service import IPAddressService
from domain.services.config_service import ConfigService
from domain.services.provider_service import ProviderService
from domain.managers.test_result_manager import TestResultManager
from services.enqueue_service import EnqueueService
from services.logger import setup_logger

logger = setup_logger(__name__)


from utils.tcping import TcpingRunner
import asyncio

class TcpingTestService:

    def __init__(self,ip_address_service: IPAddressService,pubsub_service: PubSubService,
                 config_service: ConfigService, test_result_manager: TestResultManager,
                 cache_service: CacheService,provider_service:ProviderService,
                 enqueue_service: EnqueueService
                 ):
        self.ip_address_service = ip_address_service
        self.config_service = config_service
        self.test_result_manager = test_result_manager
        self.pubsub_service = pubsub_service
        self.cache_service = cache_service
        self.provider_service=provider_service
        self.queue_service = enqueue_service
        self.semaphore = None
        self.provider_config= None 

    async def get_candidate_ips(self, provider_id: int, ip_type: str, count: int) -> List[str]:
        
        """Get candidate IPs for testing.

        Args:
            provider_id (int): The ID of the provider.
            ip_type (str): The type of IP to get (ipv4 or ipv6).
            count (int): The number of IPs to get.

        Returns:
            List[str]: A list of candidate IPs.
        """

        if ip_type == 'ipv4':
            results = await self.ip_address_service.get_ipsv4_by_provider(provider_id,  count, randomize=True)
        if ip_type == 'ipv6':
            results = await self.ip_address_service.get_ipsv6_by_provider(provider_id,  count, randomize=True)    
        logger.info(f"目录的ip{results}")        
        return [result.ip_address for result in results]
    


    async def available(self,avg_latency,packet_loss)->bool:
        if avg_latency <= self.tcping_config['avg_latency'] and  packet_loss <= self.tcping_config['packet_loss']:
            return True
        else:
            return False

    async def tcping_test_by_provider(self,  provider_id: int, user_submitted_ips: List[str] = None):
        provider = self.provider_service.get_provider_by_id(provider_id)
        self.provider_config = provider.config
                     
        logger.info(f"Starting TCPing test for provider {provider_id}")
        config =await self.provider_service.get_tcping_config(provider_id =provider_id)
        logger.info(f"config:{config}")
        tcping_port = config.get('port')
        tcping_timeout = config.get('time_out')
        ipv4_enable = config.get('ip_v4_enable')
        ipv6_enable = config.get('ip_v6_enable')
        system_config = await self.config_service.get_system_config()
        batch = system_config.get('tcping_semaphore_count')
        ips_v4=[]
        ips_v6=[]
        
        if user_submitted_ips is not None:
            ips = user_submitted_ips
        else:
            if ipv4_enable:
                ip_type = "ipv4"
                ips_v4 =await self.get_candidate_ips(provider_id, ip_type, await self.get_max_candidate())
            elif ipv6_enable:
                ip_type = "ipv4"
                ips_v6 =await self.get_candidate_ips(provider_id, ip_type, await self.get_max_candidate())
            ips = ips_v4+ips_v6
        logging.info(f"合并数据ips:{ips}")
        for i in range(0, len(ips), batch):
            batch_ips= ips[i:i + batch]
            await self._handle_tcping_test(batch_ips,tcping_port,tcping_timeout)
            

    async def _handle_tcping_test(self, ips: List[str],tcping_port,tcping_timeout):
        # gather
        tasks = []
        for ip in ips:
            tasks.append(TcpingRunner.run_with_stats(host=ip, port=tcping_port, timeout=tcping_timeout))
        await asyncio.gather(*tasks)
        
    async def batch_tcping_test_task(self,batch_test_data:BatchTestRequest):
        logger.info(f"Starting TCPing test for provider {batch_test_data.provider_ids}")
        provider_ids = batch_test_data.provider_ids
        print(self.queue_service)
        # 添加到后台执行
        task_grou_name = f"tcping_test_provider_{uuid4()}"
        for provider_id in provider_ids:
            await self.queue_service.enqueue_jobs_to_group(task_grou_name,"handle_tcping_test_by_provider",provider_id=provider_id,user_submitted_ips=None)
        await self.queue_service.start_group_jobs(task_grou_name)