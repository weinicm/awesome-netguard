import asyncio
import logging
from domain.services.redis_service import RedisManager

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class QueueService:
    _instance = None
    task_queue_key = "task_queue"  # 任务队列的键名

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(QueueService, cls).__new__(cls, *args, **kwargs)
            cls._instance.redis_manager = RedisManager()
            asyncio.run(cls._instance.init_redis())  # 确保在第一次创建实例时初始化 Redis 连接
        return cls._instance

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = QueueService()
        return cls._instance

    async def init_redis(self):
        """ 初始化 Redis 连接 """
        if not self.redis_manager.redis:
            await self.redis_manager.init_redis()
        else:
            logger.info("Redis connection already initialized")

    async def enqueue_task(self, task: str):
        """ 将任务推入任务队列 """
        try:
            await self.init_redis()
            await self.redis_manager.redis.rpush(self.task_queue_key, task)
            logger.info(f"Task enqueued: {task}")
        except Exception as e:
            logger.error(f"Failed to enqueue task: {task}. Error: {e}")

    async def dequeue_task(self) -> str:
        """ 从任务队列中取出任务并返回 """
        logger.debug("开始取任务, Starting to dequeue a task")
        try:
            logger.debug("Attempting to dequeue a task from the queue")
            task = await self.redis_manager.redis.blpop(self.task_queue_key, timeout=0)
            if task:
                # 确保 task 是一个元组
                if isinstance(task, tuple) and len(task) == 2:
                    task_value = task[1]  # 解码任务值
                    logger.info(f"Task dequeued: {task_value}")
                    return task_value
                else:
                    logger.error(f"Unexpected task format: {task}")
                    return None
            else:
                logger.debug("No task available in the queue.")
                return None
        except Exception as e:
            logger.error(f"Failed to dequeue task. Error: {e}")
            return None