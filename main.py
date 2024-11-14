from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api import config_router, iprange_router, provider_router, message_router, test_router
from dependencies import get_pubsub_service,get_db_manager,get_redis_manager
from services.logger import setup_logger
import asyncio
import uvicorn
import signal

logger = setup_logger(__name__)

# 定义 lifespan 异步上下文管理器
async def lifespan(app):
    logger.info("Starting application lifespan")

    # 初始化数据库管理器
    db = get_db_manager()
  
    logger.info(f"Database connected: {db}")

    # 初始化 Redis 管理器
    redis_manager = await get_redis_manager()
    logger.info(f"Redis manager initialized: {redis_manager}")

    # 创建 PubSubService 实例
    pubsub_service =await get_pubsub_service()
    logger.info(f"我的崆:{pubsub_service}")
    logger.info(f"PubSubService initialized: {pubsub_service}")

    # 创建一个后台任务来处理发布/订阅
    async def process_pubsub():
        try:
            # 直接传递 on_progress_update 方法
            await pubsub_service.subscribe_to_channel("progress_updates", pubsub_service.on_progress_update)
        except asyncio.CancelledError:
            logger.info("PubSub service is being cancelled")
        except Exception as e:
            logger.error(f"Failed to connect to Redis. Error: {e}")

    # 启动后台任务
    task1 = asyncio.create_task(process_pubsub())
    logger.info(f"Started background tasks for PubSub services: {task1}")

    # 返回一个异步生成器
    yield

    # 在这里进行关闭后的操作
    await db.close()
    logger.info("Database closed")

    # 取消并等待后台任务完成
    task1.cancel()
    try:
        await asyncio.wait([task1], return_when=asyncio.ALL_COMPLETED)
    except asyncio.CancelledError:
        logger.info("Background tasks for PubSub services stopped")
    finally:
        logger.info("All background tasks stopped")

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
app.include_router(iprange_router, prefix="/iprange", tags=["Ipranges"])
app.include_router(message_router, prefix="/message", tags=["MessageRouter"])
app.include_router(test_router, prefix="/test", tags=["Test_Router"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to CDNNetGuard"}

@app.get("/test_publish")
async def test_publish():
    pubsub_service = await get_pubsub_service()
    await pubsub_service.publish("progress_updates", '{"status": "in_progress", "progress": 50}')
    return {"message": "Test message published"}

# 添加 main 方法
def main():
    # 注册信号处理函数
    loop = asyncio.get_event_loop()

    def handle_shutdown():
        logger.info("Shutting down...")
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.stop()

    loop.add_signal_handler(signal.SIGINT, handle_shutdown)
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown)

    # 使用 Uvicorn 运行应用
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# 如果这个文件是主程序入口，则运行 main 方法
if __name__ == "__main__":
    main()