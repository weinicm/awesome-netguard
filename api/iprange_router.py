from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from domain.schemas.ip_range import  IPRangeCreateFromAPI, IPRangeDeleteByApi, IPRangeUpdateCidrs, IPRangeUpdateCustomRange, IPRangeUpdateSingles, IPRangesBYProviderRequest, IPRangesByProviderResponse  # 确保导入了所有需要的模型
from domain.services.ip_range_service import IPRangeService
from services.logger import setup_logger
from dependencies import get_ip_range_service

router = APIRouter()

logger = setup_logger(__name__)

@router.put("/api/update/{id}", status_code=201)
async def create_ip_range(
    iprange_data: IPRangeCreateFromAPI,
    background_tasks: BackgroundTasks,
    ip_range_service: IPRangeService = Depends(get_ip_range_service)
):
    
    try:
        logger.info(f"Scheduling IP range creation with data: {iprange_data}")
        
        # 将任务添加到后台任务队列
        background_tasks.add_task(ip_range_service.create_from_api, iprange_data)
        
        logger.info("IP range creation scheduled successfully")
        return {"message": "IP range creation scheduled1"}
    except Exception as e:
        logger.error(f"Error scheduling IP range creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/update/single/{id}", status_code=201)
async def create_ip_range(
    iprange_data: IPRangeUpdateSingles,
    background_tasks: BackgroundTasks,
    ip_range_service: IPRangeService = Depends(get_ip_range_service)
):
    
    try:
        logger.info(f"Scheduling IP range creation with data: {iprange_data}")
        
        # 将任务添加到后台任务队列
        background_tasks.add_task(ip_range_service.update_ip_range_from_single_ips, iprange_data)
        
        logger.info("IP range creation scheduled successfully")
        return {"message": "IP range creation scheduled"}
    except Exception as e:
        logger.error(f"Error scheduling IP range creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/update/cidrs/{id}", status_code=201)
async def create_ip_range(
    iprange_data: IPRangeUpdateCidrs,
    background_tasks: BackgroundTasks,
    ip_range_service: IPRangeService = Depends(get_ip_range_service)
):
    
    try:
        logger.info(f"Scheduling IP range creation with data: {iprange_data}")
        # 将任务添加到后台任务队列
        background_tasks.add_task(ip_range_service.update_ip_ranges_from_cidrs,iprange_data)
        
        logger.info("IP range creation scheduled successfully")
        return {"message": "IP range creation scheduled"}
    except Exception as e:
        logger.error(f"Error scheduling IP range creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/update/custom/{id}", status_code=201)
async def create_ip_range(
    iprange_data: IPRangeUpdateCustomRange,
    background_tasks: BackgroundTasks,
    ip_range_service: IPRangeService = Depends(get_ip_range_service)
):
    
    try:
        logger.info(f"Scheduling IP range creation with data: {iprange_data}")
        
        # 将任务添加到后台任务队列
        background_tasks.add_task(ip_range_service.update_ip_range_from_custom_ranges, iprange_data)
        
        logger.info("IP range creation scheduled successfully")
        return {"message": "IP range creation scheduled"}
    except Exception as e:
        logger.error(f"Error scheduling IP range creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))           
    
@router.delete("/api/delete/{id}",status_code=201)
async def delete_ip_range_by_api(
    iprange_data: IPRangeDeleteByApi,
    background_tasks: BackgroundTasks,
    ip_range_service: IPRangeService = Depends(get_ip_range_service)
):
    try:
        logger.info(f"Scheduling IP range deletion with data: {iprange_data}")
        
        # 将任务添加到后台任务队列
        background_tasks.add_task(ip_range_service.delete_ip_range_by_api, iprange_data)
        
        logger.info("IP range deletion scheduled successfully")
        return {"message": "IP range deletion scheduled"}
    except Exception as e:
        logger.error(f"Error scheduling IP range deletion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/provider/{provider_id}", response_model=IPRangesByProviderResponse)
async def get_ip_ranges_by_provider(
    provider_id:int,
    ip_range_service: IPRangeService = Depends(get_ip_range_service)
):
    try:
        result = await ip_range_service.get_ip_ranges_by_provider(provider_id)
        logger.info(f"我的数据是{result}")
        return result
    except Exception as e:
        logger.error(f"Error getting IP ranges by provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))