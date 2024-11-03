import aioredis
import json
from typing import Set, Callable, Awaitable
from domain.services.redis_service import RedisManager  # 假设 RedisManager 在同一个包中的 redis_manager 模块里
from fastapi.websockets import WebSocket

class PubSubService:
    _instance = None
    connected_clients: Set[WebSocket] = set()  # 用于存储所有连接的 WebSocket 客户端

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PubSubService, cls).__new__(cls, *args, **kwargs)
            cls._instance.redis_manager = RedisManager()
        return cls._instance

    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            cls._instance = PubSubService()
        return cls._instance

    async def init_redis(self):
        if not self.redis_manager.redis:
            await self.redis_manager.init_redis()

    async def publish(self, channel: str, message: str):
        """ 发布消息到指定频道 """
        await self.init_redis()
        await self.redis_manager.redis.publish(channel, message)

    async def subscribe_to_channel(self, channel: str, callback: Callable[[str], Awaitable[None]]):
        """ 订阅指定频道并设置回调函数 """
        await self.init_redis()
        pubsub = self.redis_manager.redis.pubsub()
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    await callback(message['data'])
                except Exception as e:
                    print(f"Error in callback: {e}")
            elif message['type'] == 'subscribe':
                print(f"Subscription confirmed: {message}")  # 调试信息
            else:
                print(f"Other message type: {message}")  # 调试信息

    async def unsubscribe_from_channel(self, channel: str):
        """ 取消订阅指定频道 """
        await self.init_redis()
        pubsub = self.redis_manager.redis.pubsub()
        await pubsub.unsubscribe(channel)

    @classmethod
    async def register_client(cls, websocket: WebSocket):
        cls.connected_clients.add(websocket)
        print(f"Client registered: {websocket}")  # 调试信息

    @classmethod
    async def unregister_client(cls, websocket: WebSocket):
        cls.connected_clients.discard(websocket)
        print(f"Client unregistered: {websocket}")  # 调试信息

    @classmethod
    async def broadcast_message(cls, message: dict):
        print(f"Connected clients: {cls.connected_clients}")  # 调试信息
        print(f"Broadcasting message to {len(cls.connected_clients)} clients: {message}")  # 调试信息
        for client in cls.connected_clients.copy():
            try:
                await client.send_json(message)
                print(f"Sent message to client: {client}")  # 调试信息
            except Exception as e:
                print(f"Failed to send message to client: {client}. Error: {e}")
                await cls.unregister_client(client)

    # 新增的回调函数
    async def on_progress_update(self, message_data: str):
        """ 处理进度更新消息并广播给所有客户端 """
        try:
            message = json.loads(message_data)
            await self.broadcast_message(message)
        except json.JSONDecodeError:
            print("Received non-JSON data, ignoring.")
        except Exception as e:
            print(f"An error occurred while processing the progress update: {e}")
