import asyncio
import json
from services.pubsub_service import PubSubService
from domain.managers.test_result_manager import TestResultManager
from services.logger import setup_logger
from utils.tcping import TcpingRunner
from domain.schemas.config import TcpingConfig

logger = setup_logger(__name__)

class TcpingTestService:

    def __init__(self, tcping_config:TcpingConfig, pubsub_service:PubSubService, test_result_manager:TestResultManager):
        self.tcping_config = tcping_config
        self.pubsub_service = pubsub_service
        self.test_result_manager = test_result_manager
        self.completed_tests = 0  # 初始化计数器

    async def run_tcping_test(self, ips: list):
        port = self.tcping_config.port
        timeout = self.tcping_config.time_out
        total_ips = len(ips)
        processed_ips = len(ips)
        target = self.tcping_config.count

        for i in range(0, len(ips), 20):
            if self.completed_tests >= target:  # 检查是否已达到目标
                break

            batch = ips[i:i+20]
            batch_size = len(batch)

            tasks = []
            for ip in batch:
                task = self._run_single_tcping_test(ip, port, timeout)
                tasks.append(task)

            await asyncio.gather(*tasks)
            processed_ips += batch_size

            # 发布批次的进度更新
            progress_message = json.dumps({
                "status": "in_progress",
                "progress": (processed_ips / total_ips) * 100,
                "total": total_ips,
                "processed": processed_ips
            })
            await self.pubsub_service.publish("progress_updates", progress_message)

    async def _run_single_tcping_test(self, ip, port, timeout):
        try:
            # 执行 TCPing 测试
            result = await TcpingRunner.run_with_stats(ip, port, timeout)
            if result is not None:
                # 保存测试结果
                avg_latency, std_deviation, packet_loss = result
                if self.is_available_result(avg_latency, packet_loss):
                    await self.test_result_manager.insert_test_result(ip, result)
                    self.completed_tests += 1  # 每次成功插入结果后增加计数器
            logger.info(f"TCPing test completed for {ip}")
        except Exception as e:
            logger.error(f"Failed to run TCPing test for {ip}: {e}")
            
    
    def is_available_result(self,avg_latency,packet_loss):
        if(avg_latency <= self.tcping_config.avg_latency and packet_loss <= self.tcping_config.packet_loss):
            return False
        else:
            return True