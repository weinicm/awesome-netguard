import json
from typing import Callable, Awaitable, List, Optional
from services.redis_manager import RedisManager
from services.logger import setup_logger

logger = setup_logger(__name__)

class PubSubService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PubSubService, cls).__new__(cls)
        return cls._instance

    def __init__(self, redis_manager: RedisManager):
        if not hasattr(self, 'initialized'):
            self.redis_manager = redis_manager
            self.message_queue: List[dict] = []
            self.initialized = True

    async def publish(self, channel: str, message: str):
        """ 发布消息到指定频道 """
        await self.redis_manager.publish(channel, message)

    async def subscribe_to_channel(self, channel: str, callback: Callable[[str], Awaitable[None]]):
        """ 订阅指定频道并设置回调函数 """
        pubsub = self.redis_manager.pubsub()
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            if message['type'] == 'message':
                await callback(message['data'])
            elif message['type'] == 'subscribe':
                logger.info(f"Subscription confirmed: {message}")  # 调试信息
            else:
                logger.info(f"Other message type: {message}")  # 调试信息

    async def unsubscribe_from_channel(self, channel: str):
        """ 取消订阅指定频道 """
        pubsub = self.redis_manager.pubsub()
        await pubsub.unsubscribe(channel)

    async def on_progress_update(self, message_data: bytes):
        """ 处理进度更新消息并更新最新进度信息 """
        try:
            message_str = message_data.decode('utf-8')  # 解码字节对象为字符串
            message = json.loads(message_str)

            # 将消息存放到列表中
            self.message_queue.append(message)

        except json.JSONDecodeError:
            print("Received non-JSON data, ignoring.")
        except Exception as e:
            print(f"An error occurred while processing the progress update: {e}")

    def get_message(self) -> Optional[dict]:
        """ 从消息队列中获取消息 """
        if self.message_queue:
            message = self.message_queue.pop(0)
            return message
        return None