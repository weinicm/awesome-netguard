# config_router.py

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError
from domain.schemas.config import Config, ConfigCreate, DefualtConfig
from domain.services.config_service import ConfigService
from dependencies import get_config_service

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/create", response_model=Config)
async def save_config(config: ConfigCreate, config_service: ConfigService = Depends(get_config_service)):
    try:
        # 删除已经存在的provider_id配置
        await config_service.delete_provider_config(config.provider_id)
        # 调用 ConfigService 的方法来保存配置
        config = await config_service.create_config(config)
        logger.info(f"我的config:{config}")
        return config
    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/default", response_model=DefualtConfig)
async def get_default_config(config_service: ConfigService = Depends(get_config_service)):
    try:
        # 调用 ConfigService 的方法来获取默认配置
        default_config = await config_service.get_default_config()
        return default_config
    except Exception as e:
        logger.error(f"Failed to get default config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.get("/provider/{provider_id}",response_model=Config)
async def get_provider_config(provider_id: int, config_service: ConfigService = Depends(get_config_service)):
    try: 
        
        conf = await config_service.get_config_by_provider(provider_id)
        logger.info(f"我的conf:{conf}")
        return conf
    except Exception as e:
        logger.error(f"Failed to get provider config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    


# @router.put("/update/{id}",response_model=Config)
# async def update_provider_config(config: ConfigCreate, config_service: ConfigService = Depends(get_config_service)):
#     try:
#         # 调用 ConfigService 的方法来更新提供商配置
#         updated_config = await config_service.update_config(config)
#         return updated_config
#     except ValidationError as ve:
#         logger.error(f"Validation error: {ve}")
#         raise HTTPException(status_code=400, detail=str(ve))
#     except Exception as e:
#         logger.error(f"Failed to update provider config: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")