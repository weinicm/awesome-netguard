import aioredis
from config.settings import RedisConfig

class RedisManager:
    def __init__(self):
        self.redis = None

    async def init_redis(self):
        if not self.redis:
            try:
                self.redis = aioredis.Redis(
                    host=RedisConfig.REDIS_HOST,
                    port=RedisConfig.REDIS_PORT,
                    db=RedisConfig.REDIS_DB,
                    decode_responses=True  # 如果需要解码响应
                )
                print("Redis connection initialized")  # 调试信息
            except Exception as e:
                print(f"Failed to initialize Redis: {e}")
                raise
        return self.redis

    async def close_redis(self):
        if self.redis:
            await self.redis.close()
            await self.redis.connection_pool.disconnect()
            self.redis = None