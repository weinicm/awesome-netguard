import logging
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from domain.services.config_service import ConfigService
from schemas.config import ConfigUpdate,ConfigUpdateProviders


router = APIRouter()

# 创建 ConfigService 实例
config_service = ConfigService()

@router.get("/{name}")
async def get_config(name: str):
    """
    获取指定名称的配置
    """
    try:
        result = await config_service.get_config(name=name)
        if result is None:
            raise HTTPException(status_code=404, detail="Config not found")
        return result
    except HTTPException as http_exc:
        # 如果是 HTTPException，则直接重新抛出
        raise http_exc
    except Exception as e:
        # 对于其他异常，记录错误并返回 500 错误
        logging.error(f"Error getting config with name: {name}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{id}")
async def update_config(id: int, config_data: ConfigUpdate):
    """
    更新指定 ID 的配置
    """
    try:
        result = await config_service.update_config(id, config_data.content)
        if result is None:
            raise HTTPException(status_code=404, detail="Config not found")
        return {"message": "Config updated successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_all_configs():
    """
    获取所有配置
    """
    try:
        result = await config_service.get_all_configs()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/update-monitor-list")
async def update_monitor_list(update_data: ConfigUpdateProviders):
    try:
        provider_ids = [int(id) for id in update_data.provider_ids]
        result = await config_service.update_monitor_list(provider_ids)
        return result
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        logging.error(f"Value error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-monitor-list")
async def get_monitor_list():
    try:
        result = await config_service.get_monitor_list()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

