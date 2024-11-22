import asyncio
from fastapi import APIRouter, Depends, HTTPException
from domain.schemas.test_result import TestRequest
from domain.services.tcping_test_service import TcpingTestService
from domain.services.ip_address_service import IPAddressService
from dependencies import get_tcping_test_service
from services.logger import setup_logger
from services.enqueue_service import EnqueueService
from dependencies import get_enqueue_service,get_ip_address_service
logger = setup_logger(__name__)

router = APIRouter()

lock = asyncio.Lock()
# @router.post('/provider')
# async def tcping_test_by_provider(test_data:TestRequest,
#                                   queue_service: EnqueueService = Depends(get_enqueue_service)
#                                   ):
#     async with lock:
#         try:
#             provider_id = test_data.provider_id
#             task_group = "testing"
#             await queue_service.enqueue_jobs_to_group(task_group, "store_provider_ips", provider_id=provider_id)
#             await queue_service.enqueue_jobs_to_group(task_group, "curl_test",list[str])
#             await queue_service.enqueue_jobs_to_group(task_group,"tcping_test",list[str])
#             await queue_service.start_group_jobs(task_group)
#             return {"count": "正在运行", "status": "success"}
#         except Exception as e:
#             logger.info(f"出现问题了,{e}")
#             raise HTTPException(status_code=500, detail=str(e))