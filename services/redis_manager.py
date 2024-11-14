# redis_manager.py
import os
import aioredis
from typing import Awaitable, Dict
from arq.connections import RedisSettings

class RedisManager:
    _instance = None

    @staticmethod
    async def get_instance() -> Awaitable['RedisManager']:
        if RedisManager._instance is None:
            RedisManager._instance = await aioredis.from_url(
                f"redis://{os.getenv('REDIS_HOST', 'localhost')}",
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                encoding='utf-8'
            )
        return RedisManager._instance

    @staticmethod
    def get_redis_config() -> Dict[str, str]:
        """ 返回 Redis 连接的配置信息 """
        return {
            'url': f"redis://{os.getenv('REDIS_HOST', 'localhost')}",
            'port': str(os.getenv('REDIS_PORT', 6379)),
            'db': str(os.getenv('REDIS_DB', 0)),
            'encoding': 'utf-8'
        }

    @staticmethod
    def get_redis_url() -> str:
        """ 返回 Redis 连接的 URL """
        config = RedisManager.get_redis_config()
        return f"{config['url']}:{config['port']}/{config['db']}"

    @staticmethod
    def get_arq_redis_settings() -> RedisSettings:
        """ 返回 arq 的 RedisSettings 对象 """
        config = RedisManager.get_redis_config()
        return RedisSettings(
            host=config['url'].split('//')[-1],
            port=int(config['port']),
            database=int(config['db']),
            password=None  # 如果有密码，可以在这里设置
        )

    @staticmethod
    async def close_instance():
        if RedisManager._instance:
            await RedisManager._instance.close()
            RedisManager._instance = None

    async def set(self, key: str, value: str, ex: int = None):
        """ 设置缓存项 """
        await self._instance.set(key, value, ex=ex)

    async def get(self, key: str) -> str:
        """ 获取缓存项 """
        return await self._instance.get(key)

    async def delete(self, key: str):
        """ 删除缓存项 """
        await self._instance.delete(key)