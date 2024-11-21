from fastapi import APIRouter, Depends, HTTPException,BackgroundTasks
from domain.services.ip_address_service import IPAddressService
from services.logger import setup_logger
from dependencies import get_ip_address_service

router = APIRouter()

logger = setup_logger(__name__)

@router.post("/update/provider/{id}", status_code=201)
async def update_provider(id: int, background_tasks: BackgroundTasks, ip_address_service: IPAddressService = Depends(get_ip_address_service)) -> str:
    try:
        # Add the background task to handle the store_provider_ips operation
        background_tasks.add_task(ip_address_service.store_provider_ips, provider_id=id)
        # Return a message to the client indicating that the task has been initiated
        return f"Task initiated to update provider {id} in the background."
    except Exception as e:
        logger.error(f"Error updating provider {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating provider {id}")
    