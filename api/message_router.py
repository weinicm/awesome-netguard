import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from domain.services.pubsub_service import PubSubService

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logging.debug("WebSocket endpoint called")
    await websocket.accept()
    logging.debug(f"WebSocket connection accepted: {websocket}")
    
    # 注册 WebSocket 客户端
    await PubSubService.register_client(websocket)
    logging.debug(f"Client registered: {websocket}")
    
    try:
        while True:
            # 接收来自客户端的消息
            data = await websocket.receive_text()
            logging.debug(f"Received message: {data}")
            
            # 在这里可以处理接收到的消息
            # 例如，你可以将消息发送回客户端或进行其他处理
            # await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect as e:
        logging.error(f"WebSocket disconnected: {e}")
        # 取消注册 WebSocket 客户端
        await PubSubService.unregister_client(websocket)
        logging.debug(f"Client unregistered: {websocket}")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        # 取消注册 WebSocket 客户端
        await PubSubService.unregister_client(websocket)
        logging.debug(f"Client unregistered: {websocket}")
        await websocket.close()