from domain.managers import ip_manager
from domain.managers.monitor_manager import MonitorManager
from domain.schemas.monitor import Monitor,CreateMonitor,UpdateMonitor
from services.enqueue_service import EnqueueService
from services.pubsub_service import PubSubService
from utils.tcping import TcpingRunner
from utils.curl import CurlRunner
from typing import List

class MonitorService:
    def __init__(self, monitor_manager: MonitorManager, pubsub_service: PubSubService, queue_service: EnqueueService):
        self.monitor_manager = monitor_manager
        self.pubsub_service = pubsub_service
        self.queue_service = queue_service

    async def create_monitor(self, create_monitor_data: CreateMonitor) -> Monitor:
        """
        创建一个新的监控记录
        :param create_monitor_data: 创建监控记录的数据
        :return: 创建的监控记录
        """
        # 使用 MonitorManager 创建监控记录
        monitor = await self.monitor_manager.create_monitor(create_monitor_data.to_dict())

        return monitor

    async def update_monitor(self, monitor_id: int, update_monitor_data: UpdateMonitor) -> Monitor:
        """
        更新现有的监控记录
        :param monitor_id: 监控记录的 ID
        :param update_monitor_data: 更新监控记录的数据
        :return: 更新后的监控记录
        """
        # 使用 MonitorManager 更新监控记录
        monitor = await self.monitor_manager.update_monitor(monitor_id, update_monitor_data.to_dict())

        # 发布更新监控记录的事件
        await self.pubsub_service.publish("monitor_updated", monitor.to_dict())

        return monitor

    async def delete_monitor(self, monitor_id: int) -> bool:
        """
        删除监控记录
        :param monitor_id: 监控记录的 ID
        :return: 是否成功删除
        """
        # 使用 MonitorManager 删除监控记录
        success = await self.monitor_manager.delete_monitor(monitor_id)

        if success:
            # 发布删除监控记录的事件
            await self.pubsub_service.publish("monitor_deleted", {"id": monitor_id})

        return success

    async def get_monitor(self, monitor_id: int) -> Monitor:
        """
        获取监控记录
        :param monitor_id: 监控记录的 ID
        :return: 监控记录
        """
        # 使用 MonitorManager 获取监控记录
        return await self.monitor_manager.get_monitor(monitor_id)

    async def get_all_monitors(self) -> List[Monitor]:
        """
        获取所有监控记录
        :return: 所有监控记录的列表
        """
        # 使用 MonitorManager 获取所有监控记录
        return await self.monitor_manager.get_all_monitors()

    async def get_monitors_by_provider(self, provider_id: int) -> List[Monitor]:
        """
        获取特定提供者的所有监控记录
        :param provider_id: 提供者的 ID
        :return: 特定提供者的所有监控记录的列表
        """
        # 使用 MonitorManager 获取特定提供者的所有监控记录
        return await self.monitor_manager.get_monitors_by_provider(provider_id)

    async def run_tcping(self, monitor_id: int) -> dict:
        """
        运行 Tcping 测试
        :param monitor_id: 监控记录的 ID
        :return: Tcping 测试结果
        """
        # 获取监控记录
        monitor = await self.get_monitor(monitor_id)

        # 运行 Tcping 测试
        tcping_runner = TcpingRunner()
        result = await tcping_runner.run(monitor.provider_id)

        # 发布 Tcping 测试结果
        await self.pubsub_service.publish("tcping_result", result)

        return result

    async def run_curl(self, monitor_id: int) -> dict:
        """
        运行 Curl 测试
        :param monitor_id: 监控记录的 ID
        :return: Curl 测试结果
        """
        # 获取监控记录
        monitor = await self.get_monitor(monitor_id)

        # 运行 Curl 测试
        curl_runner = CurlRunner()
        result = await curl_runner.run(monitor.provider_id)

        # 发布 Curl 测试结果
        await self.pubsub_service.publish("curl_result", result)

        return result

    async def check_provider_exists(self, provider_id: int) -> bool:
        """
        判断特定提供者是否已经存在
        :param provider_id: 提供者的 ID
        :return: 提供者是否存在
        """
        # 使用 MonitorManager 获取特定提供者的所有监控记录
        monitors = await self.monitor_manager.get_monitors_by_provider(provider_id)
        if monitors is None or len(monitors) == 0:
            return False
        else:
            return True