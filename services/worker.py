# worker.py

import os
import sys
# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
from arq import create_pool, run_worker
from domain.services.tasks import get_all_functions
from services.redis_manager import RedisManager


async def startup(ctx):
    ctx['redis'] = await create_pool(RedisManager.get_arq_redis_settings())

async def shutdown(ctx):
    await ctx['redis'].close()

class WorkerSettings:
    functions = get_all_functions()
    on_startup = startup
    on_shutdown = shutdown

if __name__ == "__main__":
    run_worker(WorkerSettings)