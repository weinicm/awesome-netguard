import asyncio
import json
import time
from typing import AsyncGenerator, Dict, List,Optional, Tuple
from utils.curl import CurlRunner
from utils.tcping import TcpingRunner
from domain.services.provider_service import ProviderService
from domain.services.ip_address_service import IPAddressService
from domain.managers.test_result_manager import TestResultManager
from globals import monitor_list

monitor_list = {}
class TestManagementService:
    def __init__(
        self,
        provider_id: int,
        default_ips_count: int = 5000,
    ):
        self.provider_service = ProviderService()  # 实例化 ProviderService
        self.provider_id = provider_id
        self.provider = self.provider_service.get_provider_by_id(provider_id)
        self.tcping_config = self.provider_service.get_tcping_config(provider_id) 
        self.curl_config = self.provider_service.get_curl_config(provider_id)  
        self.monitor_config = self.provider_service.get_monitor_config(provider_id)  
        self.ip_service = IPAddressService()
        self.test_result_manager = TestResultManager()
        self.default_ips_count = default_ips_count

    def get_ips(self, ip_type: str, count: int = None) -> List[str]:
        if count is None:
            max_count = self.default_ips_count
        else:
            max_count = count

        if ip_type == 'ipv4':
            return self.ip_service.get_ips_by_provider_v4(self.provider_id, max_count)
        elif ip_type == 'ipv6':
            return self.ip_service.get_ips_by_provider_v6
        else:
            raise ValueError("Invalid IP type. Must be one of 'ipv4', 'ipv6'.")

    async def test_with_tcping(self, ip: str) -> Tuple[str, Dict]:
        port = self.tcping_config['port']
        result = await TcpingRunner.run_with_stats(ip, port)
        return ip, result

    def handle_tcping_test_result(
        self,
        ip: str,
        result: Optional[Dict],
        valid_results_count: int,
        combined_results: Dict,
        target: int
    ) -> int:
        if result is not None and result.get('avg_latency', 0) <= self.tcping_config.get('avg_latency', 0) and \
           result.get('packet_loss', 0) <= self.tcping_config.get('packet_loss', 0):
            self.test_result_manager.save({ip: result}, self.provider_id)
            combined_results[ip] = result
            valid_results_count += 1
        return valid_results_count

    async def tcping_test(
        self,
        ip_type: str,
        user_submitted_ips: Optional[List[str]] = None,
        count: int = 5000,
        target: int = 30
    ) -> AsyncGenerator[str, None]:
        ips = user_submitted_ips if user_submitted_ips and len(user_submitted_ips) > 0 else self.get_ips(ip_type, count)

        tested_ips_count = 0
        valid_results_count = 0
        combined_results = {}
        last_heartbeat = time.time()
        chunk_size = 30

        for i in range(0, len(ips), chunk_size):
            chunk = ips[i:i + chunk_size]
            tasks = [self.test_with_tcping(ip) for ip in chunk]
            results = await asyncio.gather(*tasks)

            for ip, res in results:
                tested_ips_count += 1
                valid_results_count = self.handle_tcping_test_result(ip, res, valid_results_count, combined_results, target)

                yield f"data: {json.dumps({'total_ips': len(ips), 'tested_ips_count': tested_ips_count, 'valid_results_count': valid_results_count, 'target': target, 'combined_results': combined_results})}\n\n"

                if time.time() - last_heartbeat > 15:
                    yield ": keep-alive\n\n"
                    last_heartbeat = time.time()

                if valid_results_count >= target:
                    break

    async def curl_test(self, ip_type: str, ips: List[str]) -> AsyncGenerator[Dict, None]:
        if not self.curl_config.get('enable') or not self.curl_config.get('download_url'):
            raise ValueError("Curl test is not enabled or download_url is not set")

        async def test_single_ip(ip: str) -> Tuple[str, Dict]:
            result = await CurlRunner.run(
                ip,
                self.curl_config['download_url'],
                self.curl_config['port'],
                self.curl_config['timeout']
            )
            return ip, result

        tested_ips_count = 0
        results = {}
        last_heartbeat = time.time()
        chunk_size = 1

        for i in range(0, len(ips), chunk_size):
            chunk = ips[i:i + chunk_size]
            tasks = [test_single_ip(ip) for ip in chunk]
            completed_tasks = await asyncio.gather(*tasks)

            for ip, result in completed_tasks:
                tested_ips_count += 1
                results[ip] = result
                self.test_result_manager.update_speed(ip, result, self.provider_id)

            yield f"data: {json.dumps({'tested_ips_count': tested_ips_count, 'results': results})}\n\n"

            if time.time() - last_heartbeat > 15:
                yield ": keep-alive\n\n"
                last_heartbeat = time.time()

    async def _get_and_fill_ips(self, ip_type: str, target: int) -> AsyncGenerator[str, None]:
        better_ips = self.test_result_manager.get_better_ips(ip_type, self.provider_id)

        if len(better_ips) < target:
            await self.tcping_test(ip_type, count=target)

            better_ips = self.test_result_manager.get_better_ips(ip_type, self.provider_id)

        if self.provider_id in monitor_list:
            monitor_list[self.provider_id].clear()
        else:
            monitor_list[self.provider_id] = []
        monitor_list[self.provider_id].extend(better_ips)

    async def refresh_monitor_list(self, ip_type: str, target: int = None) -> AsyncGenerator[str, None]:
        if target is None:
            target = self.monitor_config.get('target')
        await self._get_and_fill_ips(ip_type, target)

    async def delete_monitor_list(self, ip_type: str) -> AsyncGenerator[str, None]:
        to_delete = set()
        ip_list = monitor_list.get(self.provider_id, [])

        for ip in ip_list:
            if (self.curl_config.get('speed') > ip.get('speed') or
                self.tcping_config.get('avg_latency') > ip.get('avg_latency') or
                self.tcping_config.get('packet_loss') < ip.get('packet_loss') or
                self.tcping_config.get('std_deviation') < ip.get('std_deviation')):
                to_delete.add(ip)

        for ip in to_delete:
            await self.test_result_manager.delete_ip(ip, self.provider_id)

        ip_list = [ip for ip in ip_list if ip not in to_delete]
        monitor_list[self.provider_id] = ip_list

        await self.refresh_monitor_list(ip_type)

    async def supplement_monitor_list(self, ip_type: str):
        min_ip_count = self.monitor_config.get('min_count')
        ip_list = monitor_list.get(self.provider_id, [])

        if len(ip_list) < min_ip_count:
            await self.refresh_monitor_list(ip_type, min_ip_count)

    def get_monitor_list(self) -> Dict:
        return monitor_list

    async def scheduled_curl_test(self, ip_type: str) -> AsyncGenerator[str, None]:
        test_number = self.monitor_config.get('download_test_number', 5)
        top_ips = monitor_list.get(self.provider_id, [])[:test_number]
        await self.curl_test(ip_type, top_ips)

    async def scheduled_delete_monitor_list(self, ip_type: str) -> AsyncGenerator[str, None]:
        await self.delete_monitor_list(ip_type)

    async def scheduled_supplement_monitor_list(self, ip_type: str) -> AsyncGenerator[str, None]:
        await self.supplement_monitor_list(ip_type)