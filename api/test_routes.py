import asyncio
from fastapi import APIRouter, Depends, HTTPException
from domain.services.test_service import TestService
from schemas.test_result import CurlTestRequest, TcpingTestRequest
from dependencies import get_test_service

router = APIRouter()

@router.post('/tcping')
async def tcping_test(request: TcpingTestRequest,test_service: TestService = Depends(get_test_service)):
    results = test_service.run_tcping_test(request.ip_type, request.user_submitted_ips)
    return results

@router.post('/curl')
async def curl_test(request: CurlTestRequest,test_service: TestService = Depends(get_test_service)):
    results = test_service.run_curl_test(request.ip_type)
    return results


# 创建一个锁
lock = asyncio.Lock()
@router.post('/monitor')
async def auto_test():
    async with lock:
        try:
            # 手动调用依赖函数获取 TestService 实例
            test_service = get_test_service()
            
            await test_service.start_monitoring()
            return {"count": "正在运行", "status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
