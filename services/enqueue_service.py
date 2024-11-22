from collections import deque
from arq import create_pool
import asyncio
from services.logger import setup_logger
from services.redis_manager import RedisManager

logger = setup_logger(__name__)

class EnqueueService:
    def __init__(self):
        self.redis_pool = None
        self.redis_settings = RedisManager.get_arq_redis_settings()
        self.groups = {}
        self.running_groups = set()

    async def initialize(self):
        try:
            self.redis_pool = await create_pool(self.redis_settings)
            logger.info("Redis pool initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise RuntimeError("Failed to initialize Redis pool. Initialization failed.")

    async def enqueue_job(self, function_name: str, *args, **kwargs):
        if not self.redis_pool:
            await self.initialize()
        
        return await self.redis_pool.enqueue_job(function_name, *args, **kwargs)

    async def enqueue_jobs_to_group(self, group_name: str, function_name: str, *args, **kwargs):
        if not self.redis_pool:
            await self.initialize()
        if group_name is None:
            raise ValueError("group_name must be provided")
        if group_name not in self.groups:
            self.groups[group_name] = deque()
        
        task = (function_name, args, kwargs)
        self.groups[group_name].append(task)
        logger.info(f"Task {task} added to group {group_name}")

    async def _handle_group_jobs(self, group_name: str):
        if group_name not in self.groups:
            logger.warning(f"Group {group_name} not found")
            return
        
        if group_name in self.running_groups:
            logger.warning(f"Group {group_name} is already running")
            return
        
        self.running_groups.add(group_name)
        tasks = self.groups[group_name]
        while tasks:
            task = tasks.popleft()  # 从队列中取出第一个任务
            function_name, args, kwargs = task
            job = await self.enqueue_job(function_name, *args, **kwargs)
            # logger.info(f"Job {job.job_id} added to queue for group {group_name}")
            
            while True:
                job_status = await job.status()
                # logger.info(f"Job {job.job_id} status: {job_status}")
                if job_status == 'complete':
                    logger.info(f"Job {job.job_id} completed.")
                    break
                elif job_status in ['not_found', 'deferred', 'queued', 'in_progress']:
                    # logger.info(f"Job {job.job_id} is still {job_status}. Waiting...")
                    await asyncio.sleep(1)  # 等待1秒后再次检查
                else:
                    logger.error(f"Unexpected job status: {job_status}")
                    raise ValueError(f"Unexpected job status: {job_status} for job {job.job_id}")
        
        self.running_groups.remove(group_name)

    async def start_group_jobs(self, group_name: str):
        if group_name in self.running_groups:
            logger.warning(f"Group {group_name} is already running")
            return
        
        asyncio.create_task(self._handle_group_jobs(group_name))

    async def close(self):
        if self.redis_pool:
            await self.redis_pool.close()
            self.redis_pool = None