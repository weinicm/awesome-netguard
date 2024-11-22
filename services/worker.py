import os
import sys
from arq import cron
from arq import create_pool, run_worker
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
from services.redis_manager import RedisManager
# 获取项目根目录
from domain.services.tasks import curl_test, get_all_functions,tcping_test, tcping_test_monitor_list

async def startup(ctx):
    ctx['redis'] = await create_pool(RedisManager.get_arq_redis_settings())

async def shutdown(ctx):
    await ctx['redis'].close()

class WorkerSettings:
    functions = get_all_functions()
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 1200  # 设置全局超时时间为 1200 秒（20 分钟）
    cron_josb=[
         cron(tcping_test,hour={9,12,15,18}),
         cron(tcping_test_monitor_list,hour={8,9,10,11,12,13,14,15,16,17,18},minute={30}),
         cron(curl_test,hour={8,9,10,11,12,13,14,15,16,17,18},minute={45})
    ]

if __name__ == "__main__":
    run_worker(WorkerSettings)