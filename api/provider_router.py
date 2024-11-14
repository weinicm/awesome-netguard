from typing import  List
from fastapi import APIRouter, HTTPException,  Depends
from domain.services.ip_range_service import IPRangeService
from domain.services.provider_service import ProviderService
from domain.schemas.provider import ProviderCreate, ProviderResponse, ProviderUpdate
from domain.schemas.provider import Provider
from dependencies import get_provider_service, get_config_service 
from uuid import uuid4

# 配置日志
from services.logger import setup_logger
logger = setup_logger(__name__)

router = APIRouter()

@router.post("/create", response_model=ProviderResponse)
async def create_provider(
    provider_create: ProviderCreate,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """
    创建新的提供者。

    :param provider_create: ProviderCreate 模型
    :return: 创建的 Provider 实例
    """
    provider =await provider_service.create_provider(provider_create)
    if provider:
        logger.info(f"Provider {provider} created successfully.")
        return provider
    else:
        raise HTTPException(status_code=500, detail="Failed to create provider")

@router.get("/get/{provider_id}", response_model=ProviderResponse)
async def get_provider_by_id(
    provider_id: int,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """
    根据提供商 ID 获取 Provider 实例。

    :param provider_id: 提供商的唯一标识符
    :return: Provider 实例，如果找不到则返回 404
    """
    provider = provider_service.get_provider_by_id(id)
    if provider:
        return provider
    else:
        raise HTTPException(status_code=404, detail="Provider not found")

@router.put("/update/{id}", response_model=ProviderResponse)
async def update_provider(
    id: int,
    provider_update: ProviderUpdate,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """
    更新提供商的配置信息。

    :param provider_id: 提供商的唯一标识符
    :param provider_update: ProviderUpdate 模型
    :return: 更新后的 Provider 实例，如果失败则返回 404 或 500
    """
    provider =await provider_service.update_provider(id, provider_update)
    if provider:
        logger.info(f"Provider {id} updated successfully.")
        return provider
    else:
        raise HTTPException(status_code=404, detail="Provider not found")

@router.delete("/delete/{provider_id}")
async def delete_provider(
    provider_id: int,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """
    删除提供商。

    :param provider_id: 提供商的唯一标识符
    :return: 成功删除返回 200，如果失败则返回 404 或 500
    """
    provider =await provider_service.get_provider_by_id(provider_id)
    if provider:
        await provider_service.delete_provider(provider_id)
        logger.info(f"Provider {provider_id} deleted successfully.")
        return {"message": "Provider deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Provider not found")

@router.get("/fetch-providers", response_model=List[ProviderResponse])
async def get_all_providers(
    provider_service: ProviderService = Depends(get_provider_service)
):
    """
    获取所有未删除的提供者。

    :return: Provider 实例列表
    """
    providers =await provider_service.get_all_providers()
    logger.info(f"Fetched {providers} providers.")
    return providers

# # 其他服务的路由（可选）
# @router.get("/ip-ranges", response_model=List[IPRangeCreate])
# async def get_all_ip_ranges(
#     ip_range_service: IPRangeService = Depends(get_ip_range_service)
# ):
#     """
#     获取所有 IP 范围。

#     :return: IPRange 实例列表
#     """
#     ip_ranges = ip_range_service.get_all_ip_ranges()
#     return ip_ranges

# @router.get("/ip-addresses", response_model=List[IPAddressCreate])
# async def get_all_ip_addresses(
#     ip_address_service: IPAddressService = Depends(get_ip_address_service)
# ):
#     """
#     获取所有 IP 地址。

#     :return: IPAddress 实例列表
#     """
#     ip_addresses = ip_address_service.get_all_ip_addresses()
#     return ip_addresses

# @router.post("/enqueue", response_model=EnqueueResponse)
# async def enqueue_task(
#     task: EnqueueRequest,
#     enqueue_service: EnqueueService = Depends(get_enqueue_service)
# ):
#     """
#     将任务加入队列。

#     :param task: EnqueueRequest 模型
#     :return: EnqueueResponse 实例
#     """
#     result = enqueue_service.enqueue(task)
#     return result