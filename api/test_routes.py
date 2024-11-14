import asyncio
from fastapi import APIRouter, Depends, HTTPException
from domain.services.tcping_test_service import TcpingTestService
from domain.schemas.test_result import BatchTestRequest, CurlTestRequest, TcpingTestRequest
from dependencies import get_tcping_test_service
from services.logger import setup_logger
logger = setup_logger(__name__)

router = APIRouter()

# @router.post('/tcping')
# async def tcping_test(request: TcpingTestRequest,test_service :TcpingTestService = Depends(get_tcping_test_service)):
#     results = get_tcping_test_service.run_tcping_test(request.ip_type, request.user_submitted_ips)
#     return results
# # 创建一个锁


lock = asyncio.Lock()
@router.post('/batch')
async def batch_test(batch_test_data: BatchTestRequest, tcping_test_service : TcpingTestService = Depends(get_tcping_test_service)):
    async with lock:
        try:
            await tcping_test_service.batch_tcping_test_task(batch_test_data)
            return {"count": "正在运行", "status": "success"}
        except Exception as e:
            logger.info(f"出现问题了,{e}")
            raise HTTPException(status_code=500, detail=str(e))
