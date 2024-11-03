from fastapi import APIRouter, HTTPException, Request
from domain.services.provider_service import ProviderService
from domain.services.ip_range_service import IPRangeService
from schemas1 import IPRangeInput  # 确保导入了所有需要的模型

router = APIRouter()

# 设置日志配置
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@router.put("/provider")
async def store_ip_ranges(ip_range_data: IPRangeInput, request: Request):
    """
    存储指定供应商的 IP 范围
    """
    try:
        # 打印接收到的数据
        logger.debug(f"Received IP range data: {ip_range_data}")

        # 检查 provider_id 是否存在
        if ip_range_data.provider_id is None:
            logger.error("Provider ID is missing in the request data.")
            raise HTTPException(status_code=400, detail="Provider ID is required")

        # 获取供应商信息
        provider_service = ProviderService()
        provider = await provider_service.get_provider_by_id(ip_range_data.provider_id)
        if not provider:
            logger.error(f"Provider with ID {ip_range_data.provider_id} not found")
            raise HTTPException(status_code=404, detail=f"Provider with ID {ip_range_data.provider_id} not found")

        # 检查 API URL 和 IP 范围数据
        api_url = provider.get('api_url')
        if not api_url and (not ip_range_data.cidrs and not ip_range_data.startip_endip and not ip_range_data.single_ips):
            logger.error("API URL is empty and no IP range data provided")
            raise HTTPException(status_code=400, detail="API URL is empty and no IP range data provided")

        # 创建 IPRangeService 实例
        ip_range_service = IPRangeService(provider)

        # 存储 IP 范围
        result = await ip_range_service.store_ip_ranges(ip_range_data)

        return result
    except HTTPException as http_exc:
        # 重新抛出 HTTPException 以确保 FastAPI 能够正确处理
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please check the logs for more details.")

@router.get("/provider_id/{provider_id}")
async def get_provider_ip_ranges(provider_id: int, request: Request):
    """
    获取指定供应商的所有 IP 范围
    """
    try:
        # 获取供应商信息
        provider_service = ProviderService()
        provider = await provider_service.get_provider_by_id(provider_id)
        if not provider:
            logger.error(f"Provider with ID {provider_id} not found")
            raise HTTPException(status_code=404, detail=f"Provider with ID {provider_id} not found")

        # 创建 IPRangeService 实例
        ip_range_service = IPRangeService()

        # 获取供应商的所有 IP 范围
        ip_ranges = await ip_range_service.get_ip_ranges_by_provider_id(provider_id)

        return {"provider_id": provider_id, "ip_ranges": ip_ranges}
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please check the logs for more details.")
    



# @router.put("/store_iprange/")
# async def save_ip_range(request: IPRange2IpRangeRequest):
#     # 确保 start_ip, end_ip, 和 provider_id 都不为空
#     if not request.start_ip or not request.end_ip or not request.provider_id:
#         raise HTTPException(status_code=400, detail="start_ip, end_ip, and provider_id cannot be empty")

#     # 创建 IPRangeService 实例
#     ip_range_service = IPRangeService()

#     # 保存 IP 范围
#     try:
#         await ip_range_service.create_ip_range(request)
#         return {"message": "IP range saved successfully"}
#     except Exception as e:
#         logger.error(f"Failed to save IP range: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
