from arq import Worker
from .task_service import update_ip_ranges_from_api, update_ip_ranges_cidr, update_single_ip, update_custom_range, store_provider_ips, tcping_test, curl_test, startup, shutdown
from config.settings import RedisConfig

# 定义任务函数列表
functions = [
    (update_ip_ranges_from_api, 10),
    (update_ip_ranges_cidr, 10),
    (update_single_ip, 10),
    (update_custom_range, 10),
    (store_provider_ips, 10),
    (tcping_test, 10),
    (curl_test, 10),
]

class WorkerSettings:
    functions = functions
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = None  # 默认值为 None，将在实例化时设置

    def __init__(self, redis_settings: RedisConfig):
        self.redis_settings = redis_settings