import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.pubsub_service import PubSubService
from sse_starlette.sse import EventSourceResponse
from dependencies import get_pubsub_service
from services.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

class ProgressUpdate(BaseModel):
    status: str
    progress: float
    total: int
    processed: int
    message: str


@router.get("/get_latest_message", response_model=ProgressUpdate)
async def get_latest_message(pubsub_service: PubSubService = Depends(get_pubsub_service)):
    """ 获取最新的进度信息 """
    latest_message = pubsub_service.get_latest_message()
    if latest_message is None:
        raise HTTPException(status_code=404, detail="No latest message available")
    return latest_message


# @router.get("/sse/progress")
# async def sse_progress(pubsub_service: PubSubService = Depends(get_pubsub_service)):
#     async def event_generator():
#         while True:
#             latest_message = pubsub_service.get_latest_message()
#             yield {"data": json.dumps(latest_message)}
#             await asyncio.sleep(1)  # 每秒推送一次

#     return EventSourceResponse(event_generator())

# from fastapi import Request
# from sse_starlette.sse import EventSourceResponse
# import asyncio


from fastapi import Request
from sse_starlette.sse import EventSourceResponse
import asyncio



@router.get("/sse/progress")
async def sse_progress(request: Request, pubsub_service: PubSubService = Depends(get_pubsub_service)):
    async def event_generator():
        while True:
            # 检查客户端是否断开连接
            if await request.is_disconnected():
                break

            # 获取消息
            message = pubsub_service.get_message()
            if message is not None:
                yield {"data": json.dumps(message)}

    return EventSourceResponse(event_generator())