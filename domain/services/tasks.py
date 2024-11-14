# tasks.py
from domain.services.ip_address_service import IPAddressService
from domain.services.tcping_test_service import TcpingTestService
from domain.schemas.ip_range import IPRangeCreateFromAPI,IPRangeCreateFromCidrs, IPRangeCreateFromCustomRange,IPRangeCreateFromSingleIps
from domain.services.ip_range_service import IPRangeService
from dependencies import get_ip_range_service,get_ip_address_service, get_tcping_test_service
from services.logger import setup_logger

# 配置日志
logger = setup_logger(__name__)


# 定义异步任务

async def update_ip_ranges_from_api(ctx, provider_id: int, api_url: str):
    logger.info(f"update_ip_ranges_from_api called with provider_id: {provider_id}, api_url: {api_url}")
    ip_range_service =await get_ip_range_service()
    try:
        # 确保异步操作完成后再返回结果
        result = await ip_range_service._update_ip_ranges_from_api(provider_id, api_url)
        logger.info(f"Updated IP ranges for provider {provider_id} from {api_url}")
        return result
    except Exception as e:
        logger.error(f"Failed to update IP ranges for provider {provider_id}: {e}")
        return f"Failed to update IP ranges for provider {provider_id}: {e}"

async def update_ip_ranges_cidr(ctx, provider_id: int, cidr_list: list):
    ip_range_service =await get_ip_range_service()
    cidr_data = IPRangeUpdateCidrs.model_validate({"provider_id": provider_id, "cidrs": cidr_list})
    await ip_range_service.update_ip_ranges(cidr_data)
    logger.info(f"Updated IP ranges for CIDR {cidr_data.cidrs} for provider {provider_id}")

async def update_single_ip(ctx, provider_id: int, ips: list):
    logger.info(f"ips:{ips}")
    ip_range_service =await get_ip_range_service()
    ip_update_data = IPRangeUpdateSingleIps.model_validate({"provider_id": provider_id, "single_ips": ips})
    await ip_range_service.update_single_ips(ip_update_data)
    logger.info(f"Updated single IP for provider {provider_id}")

async def update_custom_range(ctx, provider_id: int, custom_range_list: list):
    ip_range_service =await  get_ip_range_service()
    custom_range_data = IPRangeUpdateCustomRange(provider_id=provider_id, custom_ranges=custom_range_list)
    await ip_range_service.update_custom_ranges(custom_range_data)
    logger.info(f"Updated custom range {custom_range_data.custom_ranges} for provider {provider_id}")

async def store_provider_ips(ctx, *args, **kwargs):
    logger.info(f"store_provider_ips called with args: {args} and kwargs: {kwargs}")
    if args:
        provider_id = args[0]
    elif 'provider_id' in kwargs:
        provider_id = kwargs['provider_id']
    else:
        raise ValueError("No provider_id found in arguments")
    
    logger.debug(f"Arguments received: provider_id={provider_id}")
    ip_address_service =await get_ip_address_service()
    logger.info(ip_address_service)
    await ip_address_service._store_provider_ips(provider_id)

async def handle_tcping_test_by_provider(ctx, provider_id: int, user_submitted_ips: list):
    test_service = await get_tcping_test_service()
    logger.info(f"Ran TCPing test for provider {provider_id}")
    await test_service.tcping_test_by_provider(provider_id=provider_id, user_submitted_ips=user_submitted_ips)
    

async def curl_test(ctx, ip_type: str, provider_id: int, user_submitted_ips: list):
    test_service = get_tcping_test_service()
    await test_service.run_curl_test(ip_type=ip_type, provider_id=provider_id, user_submitted_ips=user_submitted_ips)
    logger.info(f"Ran Curl test for provider {provider_id}")

async def handle_tcping_test(ctx, provider_id: int, ips: list, tcping_port, tcping_timeout):
    logger.info(f"Running TCPing test for provider {provider_id}")
    try:
        tcping_test_service = get_tcping_test_service()
        await tcping_test_service._handle_tcping_test(ips=ips, tcping_port=tcping_port, tcping_timeout=tcping_timeout)
        logger.info(f"Ran TCPing test for provider {provider_id}")
    except Exception as e:
        logger.error(f"Failed to run TCPing test for provider {provider_id}: {e}")

# 获取所有任务函数
def get_all_functions():
    return [
        update_ip_ranges_from_api,
        update_ip_ranges_cidr,
        update_single_ip,
        update_custom_range,
        store_provider_ips,
        curl_test,
        handle_tcping_test,
        handle_tcping_test_by_provider
    ]