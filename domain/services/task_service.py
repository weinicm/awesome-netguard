import logging
from arq.connections import RedisSettings

from schemas.ip_range import IPRangeUpdateCidrs, IPRangeUpdateCustomRange, IPRangeUpdateIps

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置 Redis 连接
REDIS_SETTINGS = RedisSettings()

async def update_ip_ranges_from_api(ctx, provider_id: int, api_url: str):
    # 假设这里有一个 IPRangeService 实例
    ip_range_service = ctx['ip_range_service']
    await ip_range_service.update_ip_ranges_from_api(provider_id, api_url)
    logger.info(f"Updated IP ranges from API for provider {provider_id} at {api_url}")

async def update_ip_ranges_cidr(ctx, provider_id: int, cidr_list: list):
    ip_range_service = ctx['ip_range_service']
    cidr_data = IPRangeUpdateCidrs(provider_id=provider_id, cidrs=cidr_list)
    await ip_range_service.update_ip_ranges(cidr_data)
    logger.info(f"Updated IP ranges for CIDR {cidr_data.cidrs} for provider {provider_id}")

async def update_single_ip(ctx, provider_id: int, ips: list):
    ip_range_service = ctx['ip_range_service']
    ip_update_data = IPRangeUpdateIps(provider_id=provider_id, single_ips=ips)
    await ip_range_service.update_single_ips(ip_update_data)
    logger.info(f"Updated single IP for provider {provider_id}")

async def update_custom_range(ctx, provider_id: int, custom_range_list: list):
    ip_range_service = ctx['ip_range_service']
    custom_range_data = IPRangeUpdateCustomRange(provider_id=provider_id, custom_ranges=custom_range_list)
    await ip_range_service.update_custom_ranges(custom_range_data)
    logger.info(f"Updated custom range {custom_range_data.custom_ranges} for provider {provider_id}")

async def store_provider_ips(ctx, provider_id: int):
    ip_address_service = ctx['ip_address_service']
    await ip_address_service.store_provider_ips(provider_id=provider_id)
    logger.info(f"Stored provider IPs for provider {provider_id}")

async def tcping_test(ctx, ip_type: str, provider_id: int, user_submitted_ips: list):
    test_service = ctx['test_service']
    await test_service.tcping_test(ip_type=ip_type, provider_id=provider_id, user_submitted_ips=user_submitted_ips)
    logger.info(f"Ran TCPing test for provider {provider_id}")

async def curl_test(ctx, ip_type: str, provider_id: int, user_submitted_ips: list):
    test_service = ctx['test_service']
    await test_service.run_curl_test(ip_type=ip_type, provider_id=provider_id, user_submitted_ips=user_submitted_ips)
    logger.info(f"Ran Curl test for provider {provider_id}")

async def startup(ctx):
    logger.info("Task Service started")

async def shutdown(ctx):
    logger.info("Task Service stopped")