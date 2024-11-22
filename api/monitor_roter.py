import asyncio
from fastapi import APIRouter, Body, Depends, HTTPException
from dependencies import get_tcping_test_service
from domain.schemas.monitor import CreateMonitor
from domain.services.tcping_test_service import TcpingTestService
from services.logger import setup_logger
from services.enqueue_service import EnqueueService
from domain.services.monitor_service import MonitorService
from dependencies import get_enqueue_service,get_monitor_service
logger = setup_logger(__name__)

router = APIRouter()

@router.post('/provider')
async def tcping_test_by_provider(monitor_data:CreateMonitor,
                                  monitor_service: MonitorService = Depends(get_monitor_service),
                                  queue_service: EnqueueService = Depends(get_enqueue_service)
                                  ):
        try:
            provider_id = monitor_data.provider_id
            task_group = "testing"
            exist_provider = await monitor_service.check_provider_exists(provider_id)
            if not exist_provider:
                await monitor_service.create_monitor(monitor_data)
                await queue_service.enqueue_jobs_to_group(task_group, "store_provider_ips", provider_id=provider_id)                 
            await queue_service.enqueue_jobs_to_group(task_group, "tcping_test",provider_id=provider_id)
            await queue_service.enqueue_jobs_to_group(task_group,"curl_test",provider_id=provider_id)
            # no suport ipv6 test
            # await queue_service.enqueue_jobs_to_group(task_group,"tcping_test_v6",provider_id=provider_id)
            await queue_service.start_group_jobs(task_group)
            return {"count": "正在运行", "status": "success"}
        except Exception as e:
            logger.info(f"出现问题了,{e}")
            raise HTTPException(status_code=500, detail=str(e))
        
        
@router.post('/curl')
async def stop_monitor_by_provider(monitor_data:CreateMonitor,
                                   queue_service: EnqueueService = Depends(get_enqueue_service)
                                   ):
    try:
        provider_id = monitor_data.provider_id
        await queue_service.enqueue_job("curl_test")
        return {"count": "正在运行", "status": "success"}
    except Exception as e:
        logger.info(f"出现问题了,{e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
@router.get("/bestip")
async def get_best_ip(tcping_test_service: TcpingTestService = Depends(get_tcping_test_service)):
    result =await tcping_test_service.get_best_ip()
    logger.info(result)
    if result:
        return result
    else:
        return {}
    