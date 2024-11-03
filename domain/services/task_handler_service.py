import ast
import asyncio
import logging
from typing import Awaitable, Callable, Optional
from domain.services.ip_range_service import IPRangeService
from domain.services.queue_service import QueueService
from domain.services.ip_address_service import IPAddressService
from domain.services.test_service import TestService
from schemas.ip_range import IPRangeUpdateCidrs, IPRangeUpdateCustomRange, IPRangeUpdateIps

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskHandlerService:
    def __init__(
        self,
        queue_service: QueueService,
        ip_address_service: IPAddressService,
        ip_range_service: IPRangeService,
        test_service: TestService
    ):
        self.queue_service = queue_service
        self.ip_address_service = ip_address_service
        self.ip_range_service = ip_range_service
        self.test_service = test_service
        logger.info(f"TestService instance in TaskHandlerService: {type(self.test_service)}")

    async def process_task(self, task: str):
        """ 处理单个任务 """
        task_type, *args = task.split(":", 1)
        handler = self._task_handlers.get(task_type)
        if handler:
            logger.info(f"Handling task: {task}")
            await handler(*args)
        else:
            logger.warning(f"Unknown task type: {task}")

    async def consume_tasks(self):
        logger.info("11111111111111111111111111111111")
        """ 从队列中取出任务并处理 """
        while True:
            logger.debug("Starting to dequeue a task")
            task = await self.queue_service.dequeue_task()
            if task:
                logger.info(f"Task dequeued: {task}")
                logger.debug(f"处理任务: {task}")
                await self.process_task(task)
            else:
                logger.debug("No task available in the queue.")
                logger.debug("无任务,正在等待任务")
                await asyncio.sleep(1)  # 如果没有任务，等待一段时间再尝试

    @property
    def _task_handlers(self) -> dict[str, Callable[[str], Awaitable[None]]]:
        return {
            "update_ip_ranges_from_api": self._handle_update_ip_ranges_from_api,
            "update_ip_ranges_cidr": self._handle_update_ip_ranges_cidr,
            "update_single_ip": self._handle_update_single_ip,
            "update_custom_range": self._handle_update_custom_range,
            "store_provider_ips": self._handle_store_provider_ips, 
            "handle_tcping_test": self._handle_tcping_test,
            "handle_curl_test": self._handle_curl_test
        }

    async def _handle_update_ip_ranges_from_api(self, *args):
        """ 处理从 API 更新 IP 范围的任务 """
        try:
            if len(args) == 1:
                provider_id, api_url = args[0].split(":", 1)
                provider_id = int(provider_id)
                await self.ip_range_service.update_ip_ranges_from_api(provider_id, api_url)
                logger.info(f"Updated IP ranges from API for provider {provider_id} at {api_url}")
            else:
                logger.error("Update IP ranges from API task requires exactly one argument")
        except ValueError:
            logger.error(f"Invalid task arguments for update_ip_ranges_from_api: {args}")
            raise
        except Exception as e:
            logger.error(f"Failed to update IP ranges from API. Error: {e}")
            raise

    async def _handle_update_ip_ranges_cidr(self, *args):
        """ 处理更新 CIDR 的任务 """
        try:
            if len(args) == 1:
                arg = args[0]
                logger.debug(f"Received task argument: {arg}")

                # 解析参数
                provider_id, cidr_str = arg.split(":", 1)
                provider_id = int(provider_id)
                cidr_list = ast.literal_eval(cidr_str)

                # 创建 IPRangeUpdateCidrs 对象
                cidr_data = IPRangeUpdateCidrs(
                    provider_id=provider_id,
                    cidrs=cidr_list
                )

                # 调用服务方法更新 IP 范围
                await self.ip_range_service.update_ip_ranges(cidr_data)
                logger.info(f"Updated IP ranges for CIDR {cidr_data.cidrs} for provider {provider_id}")
            else:
                logger.error("Update IP ranges CIDR task requires exactly one argument")
        except ValueError as ve:
            logger.error(f"Invalid task arguments for update_ip_ranges_cidr: {args}. Error: {ve}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to update IP ranges for CIDR. Error: {e}", exc_info=True)

    async def _handle_update_single_ip(self, *args):
        """ 处理更新单个 IP 的任务 """
        try:
            if len(args) == 1:
                # 解析参数并创建 IPRangeUpdateIps 对象
                arg = args[0]
                provider_id, ipsstr = arg.split(":", 1)
                provider_id = int(provider_id)
                ips = ast.literal_eval(ipsstr)

                # 创建 IPRangeUpdateIps 对象
                ip_update_data = IPRangeUpdateIps(provider_id=provider_id, single_ips=ips)

                # 调用服务方法更新 IP
                await self.ip_range_service.update_single_ips(ip_update_data)
            else:
                logger.error("Update single IP task requires exactly one argument")
        except ValueError as ve:
            logger.error(f"Invalid task arguments for update_single_ip: {args}. Error: {ve}")
            raise
        except Exception as e:
            logger.error(f"Failed to update single IP. Error: {e}")
            raise

    async def _handle_update_custom_range(self, *args):
        """ 处理更新自定义范围的任务 """
        try:
            if len(args) == 1:
                # 解析参数并创建 IPRangeUpdateCustomRange 对象
                arg = args[0]
                provider_id, custom_range_str = arg.split(":", 1)
                provider_id = int(provider_id)
                custom_range_list = ast.literal_eval(custom_range_str)

                # 创建 IPRangeUpdateCustomRange 对象
                custom_range_data = IPRangeUpdateCustomRange(
                    provider_id=provider_id,
                    custom_ranges=[{"start_ip": cr["start_ip"], "end_ip": cr["end_ip"]} for cr in custom_range_list]
                )

                # 调用服务方法更新自定义范围
                await self.ip_range_service.update_custom_ranges(custom_range_data)
                logger.info(f"Updated custom range {custom_range_data.custom_ranges} for provider {provider_id}")
            else:
                logger.error("Update custom range task requires exactly one argument")
        except ValueError as ve:
            logger.error(f"Invalid task arguments for update_custom_range: {args}. Error: {ve}")
            raise
        except Exception as e:
            logger.error(f"Failed to update custom range. Error: {e}", exc_info=True)
            raise

    async def _handle_store_provider_ips(self, *args):
        try:
            if len(args) != 1:
                logger.error("Store provider IPs task requires exactly one argument")
                return

            arg = args[0]
            if not arg:
                logger.error("Received null task argument for store_provider_ips")
                return

            logging.debug(f"Received task argument: {arg}")
            provider_id = int(arg)

            if not isinstance(provider_id, int):
                logger.error(f"Invalid provider_id type: {type(provider_id).__name__}")
                return

            await self.ip_address_service.store_provider_ips(provider_id=provider_id)
        except ValueError as ve:
            logger.error(f"Invalid task argument format for store_provider_ips: {args}. Error: {ve}")
        except Exception as e:
            logger.error(f"Failed to store provider IPs: {e}", exc_info=True)

    async def _handle_tcping_test(self, *args):
        try:
            ip_type, provider_id, user_submitted_ips = args[0].split(":")
            provider_id = int(provider_id)
            user_submitted_ips = ast.literal_eval(user_submitted_ips) if user_submitted_ips else None
            
            await self.test_service.tcping_test(ip_type=ip_type, provider_id=provider_id, user_submitted_ips=user_submitted_ips)
        except ValueError as ve:
            logger.error(f"Invalid task argument format for tcping_test: {args}. Error: {ve}")
        except Exception as e:
            logger.error(f"Failed to run TCPing test: {e}", exc_info=True)

    async def _handle_curl_test(self, *args):
        return True
        # try:
        #     ip_type, provider_id, user_submitted_ips = args[0].split(":")
        #     provider_id = int(provider_id)
        #     user_submitted_ips = ast.literal_eval(user_submitted_ips) if user_submitted_ips else None  
        #     await self.test_service.run_curl_test(ip_type=ip_type, provider_id=provider_id, user_submitted_ips=user_submitted_ips)
        # except ValueError as ve:
        #     logger.error(f"Invalid task argument format for tcping_test: {args}. Error: {ve}")
        # except Exception as e:
        #     logger.error(f"Failed to run TCPing test: {e}", exc_info=True)