import asyncio
import json
import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from domain.models.provider import Provider
from domain.services.provider_service import ProviderService
from domain.services.ip_range_service import IPRangeService
from domain.services.ip_address_service import IPAddressService
from domain.services.queue_service import QueueService
from schemas.provider import ProviderCreate, ProviderUpdate, ProviderUpdateCurl,  ProviderUpdateMonitor, ProviderUpdateTcping
import logging
import uuid

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
router = APIRouter()

# 创建 ProviderService 实例
provider_service = ProviderService()
ip_range_service = IPRangeService()
ip_address_service = IPAddressService()
queue_service = QueueService()
#--------------当前代码provider和ip_range,ip混在一起了,下一次有空的时候再分开吧.这种任务最好是新建一个应用层的service进行处理--------------- 

@router.post("/create-provider-with-ip-ranges/")
async def create_provider_with_ip_ranges(request: Request):
    try:
        # 读取请求体
        body = await request.json()
        logging.debug(f"Received request body: {body}")
        
        # 解析并验证 Provider 数据
        provider_data = body
        if not provider_data:
            raise HTTPException(status_code=400, detail="Missing 'provider' data in request body")
        
        # 将 config 字段转换为 JSON 字符串
        provider_data["config"] = json.dumps(provider_data.get("config"))
        
        provider_create_model = ProviderCreate(**provider_data)
        
        # 创建 Provider
        provider = await provider_service.create_provider(provider_create_model)
        provider_id = provider.id
        
        # 获取 cidrs, single_ips, custom_ranges, api_url
        cidrs = body.get("cidrs", [])
        single_ips = body.get("single_ips", [])
        custom_ranges = body.get("custom_ranges", [])
        api_url = body.get("api_url")
        logging.info(f"Provider {provider_id} created successfully.")
        # 将每个任务放入消息队列
        if api_url:
            task = f"update_ip_ranges_from_api:{provider_id}:{api_url}"
            await queue_service.enqueue_task(task)

        if cidrs:
            task = f"update_ip_ranges_cidr:{provider_id}:{cidrs}"
            await queue_service.enqueue_task(task)

        if single_ips:
            logging.info(f"single_ips: {single_ips}")
            task = f"update_single_ip:{provider_id}:{single_ips}"
            await queue_service.enqueue_task(task)

        if custom_ranges:
            task = f"update_custom_range:{provider_id}:{custom_ranges}"
            await queue_service.enqueue_task(task)
        
        # 在后台异步运行更新 IP 地址的任务
        task =f'store_provider_ips:{provider_id}'
        await queue_service.enqueue_task(task)
        return {"provider_id": provider_id}
    
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/")
async def get_providers():
    return await provider_service.get_providers()

@router.get("/name/{name}")
async def get_provider_by_name(name: str):
    try:
        result = await provider_service.get_provider_by_name(name)
        if result is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{provider_id}")
async def delete_provider(provider_id: int):
    try:
       result = await provider_service.delete_provider(provider_id)
       return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/id/{provider_id}")
async def get_provider_by_id(provider_id: int):
    try:
        result = await provider_service.get_provider_by_id(provider_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/delete/{provider_id}")
# async def delete_provider(provider_id: int):
#     try:
#         result = await provider_service.delete_provider(provider_id)
#         if result is None:
#             raise HTTPException(status_code=404, detail="Provider not found")
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/update/{provider_id}")
async def update_provider(provider_id: int, provider_data: ProviderUpdate):
    try:
        print(provider_data)
        result = await provider_service.update_provider_fields(provider_id, provider_data)
        print(result)
        if result is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result
    except Exception as e:
        logging.error(f"Error updating provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tcping/update/{provider_id}")
async def update_provider_tcping(provider_id: int, tcping_data: ProviderUpdateTcping):
    try:
        logging.debug(f"检查客户端信息:{tcping_data}")
        result = await provider_service.update_provider_tcping(provider_id, tcping_data)
        if result is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result
    except Exception as e:
        logging.error(f"Error updating provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/curl/update/{provider_id}")
async def update_provider_curl(provider_id: int, curl_data: ProviderUpdateCurl):
    try:
        result = await provider_service.update_provider_curl(provider_id, curl_data)
        if result is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from domain.models.provider import Provider
from schemas.provider import ProviderUpdateMonitor

@router.put("/monitor/update/{provider_id}")
async def update_provider_monitor(
    provider_id: int, 
    monitor_data: ProviderUpdateMonitor
) -> Optional[Provider]:
    """
    Updates the monitoring settings of a provider.

    :param provider_id: The ID of the provider to update.
    :param monitor_data: The monitoring data to update the provider with.
    :return: The updated provider object with the updated monitoring settings, or None if the provider does not exist.
    :raises HTTPException: If the provider is not found or if an error occurs during the update.
    """
    try:
        result = await provider_service.update_provider_monitor(provider_id, monitor_data)
        if result is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    


