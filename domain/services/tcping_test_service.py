import asyncio
import json
from typing import List
from domain.schemas.ipaddress import IPAddress
from services.pubsub_service import PubSubService
from domain.managers.test_result_manager import TestResultManager
from services.logger import setup_logger
from utils.tcping import TcpingRunner
from domain.schemas.config import TcpingConfig

logger = setup_logger(__name__)

class TcpingTestService:

    def __init__(self,pubsub_service:PubSubService,test_result_manager:TestResultManager):
        self.tcping_config = None
        self.pubsub_service = pubsub_service
        self.test_result_manager = test_result_manager
        self.completed_tests = 0  # 初始化计数器



    async def set_tcping_config(self, tcping_config: TcpingConfig):
        self.tcping_config = tcping_config


    async def run_tcping_test(self, ips: List[str]=None):
        if self.tcping_config is None:
            raise Exception("TcpingConfig is not set,Please call set_tcping_config method first")
 
        ips = ips
        logger.info(f"ips info:{ips}")
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
        if self.tcping_config is None:
            raise Exception("TcpingConfig is not set,Please call set_tcping_config method first")
        try:
            # 执行 TCPing 测试
            logger.info(f"开始tcping测试{ip}")
            result = await TcpingRunner.run_with_stats(ip, port, timeout)
            logger.info(f"返回值:{result}")
            if result is not None:
                # 保存测试结果
                _,avg_latency, std_deviation, packet_loss = result
                insert_data = {}
                if self.is_available_result(avg_latency, packet_loss):
                    logger.info(f"数据验证成功")   
                    insert_data['ip'] = ip
                    insert_data['avg_latency']= avg_latency
                    insert_data['std_deviation']=std_deviation
                    insert_data['packet_loss']=packet_loss
                    await self.test_result_manager.insert_test_result(insert_data)
                    self.completed_tests += 1  # 每次成功插入结果后增加计数器
                else:
                    logger.info(f"数据验证失败")
            logger.info(f"TCPing test completed for {ip}")
        except Exception as e:
            logger.error(f"Failed to run TCPing test for {e}")
            
    
    def is_available_result(self,avg_latency,packet_loss):
        if self.tcping_config is None:
            raise Exception("TcpingConfig is not set,Please call set_tcping_config method first")
        if(avg_latency <= self.tcping_config.avg_latency and packet_loss <= self.tcping_config.packet_loss):
            return True
        else:
            return False
        
        
    async def get_better_ips(self,count: int = 1) -> List[str]:
        results = await self.test_result_manager.get_better_ips(count)
        if results:
            return [result.ip for result in results]
        else:
            return []
    
    async def get_best_ip(self):
        return await self.test_result_manager.get_best_ip()
    
        
    async def delete_invalid_ips_by_tcping_option(self):
        if self.tcping_config is None:
            raise Exception("TcpingConfig is not set,Please call set_tcping_config method first")
        max_avg_latency = self.tcping_config.avg_latency
        max_loss_packet = self.tcping_config.packet_loss        
        await self.test_result_manager.delete_invalid_ips_by_tcping_config(max_avg_latency,max_loss_packet)
        
    async def delete_by_ip(self,ip: str):
        await self.test_result_manager.delete_test_result_by_ip(ip)