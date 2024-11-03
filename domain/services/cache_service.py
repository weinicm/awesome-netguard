# domain/services/cache_service.py

from domain.services.redis_service import RedisManager

class CacheService:
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager

    def set_cache(self, key: str, value: str, ex: int = None):
        """
        设置缓存项
        :param key: 缓存键
        :param value: 缓存值
        :param ex: 过期时间（秒）
        """
        self.redis_manager.set(key, value, ex=ex)

    def get_cache(self, key: str) -> str:
        """
        获取缓存项
        :param key: 缓存键
        :return: 缓存值，如果不存在则返回 None
        """
        return self.redis_manager.get(key)

    def delete_cache(self, key: str):
        """
        删除缓存项
        :param key: 缓存键
        """
        self.redis_manager.delete(key)