import logging
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from arq import Worker
from arq.connections import RedisSettings
from domain.services.task_service import startup, shutdown
from domain.services.worker_service import functions
from domain.services.redis_service import RedisManager
from domain.services.pubsub_service import PubSubService
from api import config_router, iprange_router, provider_router, message_router, test_router
from db.dbmanager import DBManager
from config.settings import RedisConfig
from functools import partial

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 处理任务队列的后台任务
async def process_task_queue():
    # 初始化 ARQ 工作者
    worker = Worker(
        functions=functions,
        on_startup=startup,
        on_shutdown=shutdown,
        redis_settings=RedisSettings(
            host=RedisConfig.REDIS_HOST,
            port=RedisConfig.REDIS_PORT,
            database=RedisConfig.REDIS_DB
        )
    )

    logger.info("Starting ARQ worker")
    try:
        await worker.async_run()
    except Exception as e:
        logger.error(f"ARQ worker encountered an error: {e}")
    finally:
        logger.info("ARQ worker stopped")

# 定义 lifespan 异步上下文管理器
async def lifespan(app):
    # 初始化数据库管理器
    db = DBManager()
    await db.connect()
    logger.info("Database connected")

    # 初始化 RedisManager
    redis_manager = RedisManager()
    await redis_manager.init_redis()
    logger.info("Redis connection initialized")

    # 创建一个后台任务来处理发布/订阅
    async def process_pubsub():
        try:
            pubsub_service = await PubSubService.get_instance()
            callback = partial(pubsub_service.on_progress_update)
            await pubsub_service.subscribe_to_channel("progress_updates", callback)
        except asyncio.CancelledError:
            logger.info("PubSub service is being cancelled")
        except Exception as e:
            logger.error(f"Failed to connect to Redis. Error: {e}")

    # 启动后台任务
    task1 = asyncio.create_task(process_task_queue())
    task2 = asyncio.create_task(process_pubsub())

    logger.info("Started background tasks for Queue and PubSub services")

    # 返回一个异步生成器
    yield

    # 在这里进行关闭后的操作
    await db.close()
    logger.info("Database closed")

    # 关闭 Redis 连接
    await redis_manager.close_redis()
    logger.info("Redis connection closed")

    # 取消并等待后台任务完成
    task1.cancel()
    task2.cancel()
    try:
        await task1
        await task2
    except asyncio.CancelledError:
        pass

    logger.info("Background tasks for Queue and PubSub services stopped")

# 创建 FastAPI 应用实例，并传入 lifespan 参数
app = FastAPI(lifespan=lifespan)

# 配置跨域，开发环境使用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境中应限制为具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(provider_router, prefix="/provider", tags=["Provider"])
app.include_router(config_router, prefix="/config", tags=["Config"])
app.include_router(iprange_router, prefix="/ipranges", tags=["Ipranges"])
app.include_router(message_router, prefix="/message", tags=["MessageRouter"])
app.include_router(test_router, prefix="/test", tags=["Test_Router"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to CDNNetGuard"}

# 添加 main 方法
def main():
    # 使用 Uvicorn 运行应用
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# 如果这个文件是主程序入口，则运行 main 方法
if __name__ == "__main__":
    main()