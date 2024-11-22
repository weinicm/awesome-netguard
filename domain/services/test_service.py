from datetime import datetime
import logging
import ipaddress
from typing import List, Dict, Any, Tuple
from domain.services.ip_address_service import IPAddressService
from domain.services.config_service import ConfigService
from domain.managers.test_result_manager import TestResultManager
from services.cache import CacheService
from domain.services.provider_service import ProviderService
from utils.tcping import TcpingRunner
from utils.curl import CurlRunner
import asyncio

class TestService:

    def __init__(self,provider_id:int, ip_address_service: IPAddressService,
                 config_service: ConfigService, test_result_manager: TestResultManager,cache_service: CacheService,
                 provider_service: ProviderService):
        self.provider_id = provider_id
        self.ip_address_service = ip_address_service
        self.config_service = config_service
        self.test_result_manager = test_result_manager
        # self.pubsub_service = pubsub_service
        # self.queue_service = queue_service
        self.cache_service = cache_service
        self.provider_service = provider_service
        self.tcping_semaphore = None
        self.curl_semaphore = None
        self.monitor_config = None
        self.tcping_config = None
        self.curl_config = None
        self.system_config = None

        asyncio.create_task(self.initialize_configs(provider_id))

    async def initialize_configs(self,provider_id:int):
        # 初始化所有配置信息
        self.system_config = await self.config_service.get_system_config()
        self.provider_ids = await self.config_service.get_monitor_list()
        self.monitor_config = await self.config_service.get_monitor_config()
        self.tcping_config = await self.config_service.get_tcping_config()
        self.curl_config = await self.config_service.get_curl_config()
        

    async def tcping_test(self, ip_type: str, provider_id: int, user_submitted_ips: List[str] = None):
        try:
            self.tcping_semaphore = asyncio.Semaphore(self.system_config.get('tcping_semaphore_count', 20))

            # Determine the list of IPs to test
            if user_submitted_ips:
                ips = user_submitted_ips
            elif provider_id:
                ips = await self.get_candidate_ips(provider_id, ip_type, self.system_config.get('max_candidate'))
            else:
                raise ValueError("Either 'user_submitted_ips' or 'provider_id' must be provided.")

            # Exit if TCPing is disabled in the configuration
            if self.tcping_config.get('enable', 'false') in ['false', False]:
                logging.info("TCPing is disabled in the configuration. Skipping test.")
                return

            total_ips = len(ips)
            target_value = self.monitor_config.get('count')
            current_value = 0

            # Event to signal when to stop testing
            stop_event = asyncio.Event()

            # Asynchronous function to test a single IP
            async def test_ip(ip: str):
                nonlocal current_value
                async with self.tcping_semaphore:
                    if stop_event.is_set():
                        return None

                    try:
                        result = await TcpingRunner.run_with_stats(ip, self.tcping_config.get('port'), self.tcping_config.get('time_out'))
                        if result is None:
                            logging.info(f"Test result error  return none: {ip}")
                            return None
                        host, avg_latency, std_deviation, packet_loss = result

                        test_result = TestResult(
                            ip=host,
                            avg_latency=avg_latency,
                            std_deviation=std_deviation,
                            packet_loss=packet_loss,
                            download_speed=None,
                            is_locked=False,
                            status='completed',
                            test_time=datetime.now().timestamp(),
                            is_delete=False
                        )

                        if await self.tcpingPassedIp(avg_latency, packet_loss):
                            result = await self.test_result_manager.insert_test_result(test_result.to_dict())
                            if result:
                                current_value += 1
                                if current_value >= target_value:
                                    stop_event.set()
                    except Exception as e:
                        logging.error(f"Error testing IP {ip}: {e}")
                        return None

            # Create a list of tasks for testing IPs
            tasks = [test_ip(ip) for ip in ips]

            # Execute tasks and handle completion
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            # Wait for the stop event to be set
            await stop_event.wait()

            # Cancel all remaining tasks
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

        except Exception as e:
            logging.error(f"An error occurred during the tcping test: {e}", exc_info=True)
    

    # async def curl_test(self, ip_type: str, provider_id: int, user_submitted_ips: List[str] = None):
    #     try:
    #         self.tcping_semaphore = asyncio.Semaphore(1)

    #         # Determine the list of IPs to test
    #         if user_submitted_ips:
    #             ips = user_submitted_ips
    #         elif provider_id:
    #             results = await self.test_result_manager.get_better_test_result_ip(provider_id)
    #             ips = [result['ip'] for result in results][:self.monitor_config.get('download_test_number')]
    #         else:
    #             raise ValueError("Either 'user_submitted_ips' or 'provider_id' must be provided.")

    #         # Exit if TCPing is disabled in the configuration
    #         if self.curl_config.get('enable') in ['false', False] or self.curl_config.get('download_url') is None:
    #             logging.info("Curl is disabled in the configuration. Skipping test.")
    #             return

    #         # Event to signal when to stop testing
    #         stop_event = asyncio.Event()
    #         # Asynchronous function to test a single IP
    #         async def test_ip(ip: str):
    #             async with self.tcping_semaphore:
    #                 if stop_event.is_set():
    #                     return None

    #                 try:
    #                     result = await CurlRunner.run(ip, , self.tcping_config.get('time_out'))
    #                     if result is None:
    #                         logging.info(f"Test result error  return none: {ip}")
    #                         return None
    #                     host, avg_latency, std_deviation, packet_loss = result

    #                     test_result = TestResult(
    #                         ip=host,
    #                         avg_latency=avg_latency,
    #                         std_deviation=std_deviation,
    #                         packet_loss=packet_loss,
    #                         download_speed=None,
    #                         is_locked=False,
    #                         status='completed',
    #                         test_time=datetime.now().timestamp(),
    #                         is_delete=False
    #                     )

    #                     if await self.tcpingPassedIp(avg_latency, packet_loss):
    #                         result = await self.test_result_manager.insert_test_result(test_result.to_dict())
    #                         if result:
    #                             current_value += 1
    #                             if current_value >= target_value:
    #                                 stop_event.set()
    #                 except Exception as e:
    #                     logging.error(f"Error testing IP {ip}: {e}")
    #                     return None

        #     # Create a list of tasks for testing IPs
        #     tasks = [test_ip(ip) for ip in ips]

        #     # Execute tasks and handle completion
        #     done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        #     # Wait for the stop event to be set
        #     await stop_event.wait()

        #     # Cancel all remaining tasks
        #     for task in pending:
        #         task.cancel()
        #     await asyncio.gather(*pending, return_exceptions=True)

        # except Exception as e:
        #     logging.error(f"An error occurred during the tcping test: {e}", exc_info=True)


    async def run_tcping_test(self, ip_type: str, provider_id: int, user_submitted_ips: List[str] = None):
        """
        Run the TCPing test asynchronously by pushing the task to the queue.

        Args:
            ip_type (str): The type of IP to test (ipv4 or ipv6).
            provider_id (int): The ID of the provider.
            user_submitted_ips (List[str], optional): A list of user-submitted IPs. Defaults to None.
        """
        try:
            # 将整个 tcping_test 任务推送到队列中
            task =f"handle_tcping_test:{ip_type}:{provider_id}:{user_submitted_ips}"
            await self.queue_service.enqueue_task(task)
            logging.debug(f"TCPing test task pushed to queue: {task}")
        except Exception as e:
            logging.error(f"加载任务失败,An error occurred while running tcping test: {e}")

    async def run_curl_test(self, ip_type: str, provider_id: int, user_submitted_ips: List[str] = None):
        """
        Run the curl test asynchronously by pushing the task to the queue.

        Args:
            ip_type (str): The type of IP to test (ipv4 or ipv6).
            provider_id (int): The ID of the provider.
            user_submitted_ips (List[str], optional): A list of user-submitted IPs. Defaults to None.
        """
        # Create a curl test task
        task =f"handle_curl_test:{ip_type}:{provider_id}:{user_submitted_ips}"
        # Enqueue the task for execution
        await self.queue_service.enqueue_task(task)
    
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
        return [result.ip_address for result in results]

    async def tcpingPassedIp(self, avg_latency: str, packet_loss: float):
        logging.debug(f"tcping_config:{self.tcping_config}")
        logging.debug(f"测试结果: {avg_latency}, {packet_loss}")
        logging.debug(f"预期结果packet_loss:{self.tcping_config['packet_loss']},avg_latency:{self.tcping_config['avg_latency']}")
        try:
            if avg_latency <= self.tcping_config['avg_latency'] and  packet_loss <= self.tcping_config['packet_loss']:
                return True
            else:
                return True
        except Exception as e:
            logging.error(f"An error occurred while checking if tcping passed: {e}")
            return False
        
    async def curlPassedIp(self, download_speed: float):
        try:
            if download_speed >= self.curl_config['speed']:
                return True
            else:
                return False
        except Exception as e:
            logging.error(f"An error occurred while checking if curl passed: {e}")
            return False
    
    async def lock_test_ip(self, ip: str):
        try:
            await self.test_result_manager.lock_ip(ip)
            return True
        except Exception as e:
            logging.error(f"An error occurred while locking IP: {e}")
            return False
        
    
    async def unlock_test_ip(self, ip: str):
        try:
            await self.test_result_manager.unlock_ip(ip)
            return True
        except Exception as e:
            logging.error(f"An error occurred while unlocking IP: {e}")
            return False    
        
    async def delete_test_result_by_ip(self, ip: str) -> bool:
        try:
            await self.test_result_manager.delete_test_result_by_ip(ip)
            return True
        except Exception as e:
            logging.error(f"An error occurred while deleting test result: {e}")
            return False
        
        


    async def get_better_ip_v6(self, provider_id: int) -> List[str]:
       list_v6= self.cache_service.get_cache("better_ip_v6" + str(provider_id))
       if list_v6 is None:
           _, list_v6 = await self.get_better_ip(provider_id)
           self.cache_service.set_cache("better_ip_v6" + str(provider_id), list_v6,3600)
       return list_v6
    
    async def get_better_ip_v4(self, provider_id: int) -> List[str]:
       list_v4= self.cache_service.get_cache("better_ip_v4" + str(provider_id))
       if list_v4 is None:
            list_v4, _ = await self.get_better_ip(provider_id)
            self.cache_service.set_cache("better_ip_v4" + str(provider_id), list_v4, 3600)
       return list_v4
    

    #async def auto_supplement(self,provider_id) -> None:
    async def auto_delete(self,provider_id) -> None:
        test_resultsv4 : list[TestResult] = await self.cache_service.get_cache("better_ip_v4" + str(provider_id))
        test_resultsv6: list[TestResult] = await self.cache_service.get_cache("better_ip_v6" + str(provider_id))
        test_results = test_resultsv4 + test_resultsv6
        if test_results is not None:
            for reuslt in test_results:
                if await self.tcpingPassedIp(avg_latency=0, packet_loss=0) or await self.curlPassedIp(download_speed=0):
                    await self.delete_test_result_by_ip(reuslt.ip)
    

    async def auto_supplement(self,provider_id) -> None:
        """
        Automatically supplement the better IP list for a provider.

        This method will check the current number of better IPs for a provider and
        start a TCPing test if the number is less than the minimum required.

        Args:
            provider_id (int): The ID of the provider.
        """
        reuslt_v4, reuslt_v6 = await self.get_better_ip(provider_id)
        if reuslt_v4 is None or len(reuslt_v4) < self.monitor_config['min_count']:
            self.run_tcping_test('ipv4', provider_id)
        if reuslt_v6 is None or len(reuslt_v6) < self.monitor_config['min_count']:
            self.run_tcping_test('ipv6', provider_id)        
        else:
            return

    async def auto_test(self,provider_id) -> None:
        ipv4,ipv6 = await self.get_better_ip(provider_id)
        try:
            if ipv4 is not None:
                await self.tcping_test('ipv4', provider_id,ipv4)
            if ipv6 is not None:
                await self.tcping_test('ipv6', provider_id,ipv6)    
            # 刷新ipv4,ipv6
            ipv4,ipv6 = await self.get_better_ip(provider_id)
            if ipv4 is not None:
                await self.curl('ipv4', provider_id,ipv4[:self.monitor_config['download_test_number']])
            if ipv6 is not None:
                await self.curl_test('ipv6', provider_id,ipv6[:self.monitor_config['download_test_number']])
            return True
        except Exception as e:
            return False

    
    async def start_monitoring(self) -> bool:
        try:
            provider_ids = await self.config_service.get_monitor_list()
            config = await self.config_service.get_tcping_config()
            enable_tcping = config.get('enable')
            config = await self.config_service.get_tcping_config()
            enable_tcping_ipv4 = config.get('ip_v4_enable')
            config = await self.config_service.get_tcping_config()
            enbale_tcping_ipv6 = config.get('ip_v6_enable')
            conifg = await self.config_service.get_curl_config()
            enable_curl = conifg.get('enable') and conifg.get('download_url')
            config = await self.config_service.get_curl_config()
            enable_curl_ipv4 = config.get('ip_v4_enable')
            config = await self.config_service.get_curl_config()
            enable_curl_ipv6 = config.get('ip_v6_enable')
            if provider_ids is None:
                return False
            for id in provider_ids:
                if enable_tcping and enable_tcping_ipv4:
                    await self.run_tcping_test(ip_type='ipv4', provider_id=id)
                if enable_tcping and enbale_tcping_ipv6:
                    await self.run_tcping_test(ip_type='ipv6', provider_id=id)
                if enable_curl and enable_curl_ipv4:
                    await self.run_curl_test(ip_type='ipv4', provider_id=id)
                if enable_curl and enable_curl_ipv6:
                    await self.run_curl_test(ip_type='ipv6', provider_id=id)
        except Exception as e:
            logging.error(f"An error occurred while starting monitoring: {e}")
        return True

    

