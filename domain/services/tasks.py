# tasks.py
from typing import List
import arq
from dependencies import get_ip_range_service,get_ip_address_service, get_tcping_test_service,get_config_service,get_curl_test_service,get_provider_service
from domain.schemas.config import CurlConfig, TcpingConfig
from domain.schemas.test_result import TestResult
from domain.services.config_service import ConfigService
from domain.services.curl_test_service import CurlTestService
from domain.services.tcping_test_service import TcpingTestService
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
    await ip_address_service.store_provider_ips(provider_id)

async def tcping_test(ctx,provider_id: int = None):
    if provider_id is None:
        logger.info(f"从数据库中获取id")
        provier_service = await get_provider_service()
        #这个方法临时用的,没时间处理了
        provider_id = await provier_service.get_provider_id()
    config_service:ConfigService = await get_config_service()
    tcping_config = await config_service.get_provider_tcping_config(provider_id=provider_id)
    test_service = await get_tcping_test_service()
    await test_service.set_tcping_config(tcping_config)
    ipaddress_service = await get_ip_address_service()
    ips =await ipaddress_service.get_provier_ips(provider_id=provider_id)
    if ips:
        await test_service.run_tcping_test(ips=ips)
    
    
async def tcping_test_monitor_list(ctx,provider_id: int = None):
    if provider_id is None:
        logger.info(f"从数据库中获取id")
        provier_service = await get_provider_service()
        #这个方法临时用的,没时间处理了
        provider_id = await provier_service.get_provider_id()
    config_service = await get_config_service()
    tcping_config :TcpingConfig =await config_service.get_provider_tcping_config(provider_id=provider_id)
    tcping_test_service:TcpingTestService =await get_tcping_test_service()
    await tcping_test_service.set_tcping_config(tcping_config)
    ips = await tcping_test_service.get_better_ips(tcping_config.count)    
    for ip in ips:
        # 逻辑有问题,先删除他们
            tcping_test_service.delete_by_ip(ip)
    # if test_result less tcping_config.out then get ips from ipaddress_service
    if len(ips) < tcping_config.count:
        ipaddress_service = await get_ip_address_service()
        ips =await ipaddress_service.get_provier_ips(provider_id=provider_id)
    await tcping_test_service.run_tcping_test(ips=ips)

# async def tcping_test_v6(ctx,provider_id: int):
#     config_service:ConfigService = await get_config_service()
#     tcping_config = await config_service.get_provider_tcping_config(provider_id=provider_id)
#     test_service = await get_tcping_test_service()
#     await test_service.set_tcping_config(tcping_config)
#     ipaddress_service = await get_ip_address_service()
#     ips =await ipaddress_service.get_provider_ips_v6(provider_id=provider_id)
#     await test_service.run_tcping_test(ips)
    

async def curl_test(ctx,provider_id: int = None):
    if provider_id is None:
        logger.info(f"从数据库中获取id")
        provier_service = await get_provider_service()
        #这个方法临时用的,没时间处理了
        provider_id = await provier_service.get_provider_id()
    config_service:ConfigService =await get_config_service()
    tcping_test_service:TcpingTestService =await get_tcping_test_service()
    curl_test_service:CurlTestService = get_curl_test_service()
    config =await config_service.get_provider_curl_config(provider_id=provider_id)
    ips =await tcping_test_service.get_better_ips(count=config.count)
    curl_test_service.set_tcping_config(curl_config=config)
    await curl_test_service.run_curl_test(ips)
    await curl_test_service.delete_invalid_ips_by_curl_option()
    


# 获取所有任务函数
def get_all_functions():
    return [
        update_ip_ranges_from_api,
        store_provider_ips,
        curl_test,
        tcping_test,
        tcping_test_monitor_list
    ]