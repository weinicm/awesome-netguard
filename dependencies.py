from dependency_injector import containers, providers
from db.db_manager import DBManager
from services.redis_manager import RedisManager
from domain.services.cache_service import CacheService
from services.pubsub_service import PubSubService
from domain.services.ip_address_service import IPAddressService
from domain.services.config_service import ConfigService
from domain.managers.test_result_manager import TestResultManager
from domain.services.provider_service import ProviderService
from domain.services.tcping_test_service import TcpingTestService
from domain.services.ip_range_service import IPRangeService
from domain.managers.ip_manager import IpaddressManager
from domain.managers.ip_range_manager import IPRangeManager
from domain.managers.provider_manager import ProviderManager
from services.enqueue_service import EnqueueService

# 设置日志记录
from services.logger import setup_logger
logger = setup_logger(__name__)

async def init_redis_manager():
    redis_manager = await RedisManager.get_instance()
    logger.info('Redis Manager initialized')
    return redis_manager

class ApplicationContainer(containers.DeclarativeContainer):

    # 单例管理器
    db_manager = providers.Singleton(DBManager)
    
    # 异步资源管理
    redis_manager = providers.Resource(init_redis_manager)

    # 服务
    ipaddress_manager = providers.Factory(IpaddressManager, db_manager=db_manager)
    ip_range_manager = providers.Factory(IPRangeManager, db_manager=db_manager)
    provider_manager = providers.Factory(ProviderManager, db_manager=db_manager)
    pubsub_service = providers.Singleton(PubSubService, redis_manager=redis_manager)
    cache_service = providers.Factory(CacheService, redis_manager=redis_manager)
    config_service = providers.Factory(ConfigService)
    test_result_manager = providers.Factory(TestResultManager, db_manager=db_manager)
    provider_service = providers.Factory(
        ProviderService,
        provider_manager=provider_manager,
        pubsub_service=pubsub_service
    )
    ip_address_service = providers.Factory(
        IPAddressService,
        ip_manager=ipaddress_manager,
        ip_range_manager=ip_range_manager,
        provider_manager=provider_manager,
        pubsub_service=pubsub_service
    )

    ip_range_service = providers.Factory(
        IPRangeService,
        ip_range_manager=ip_range_manager,
        pubsub_service=pubsub_service
    )
    enqueue_service = providers.Factory(
        EnqueueService
    )
    
    tcping_test_service = providers.Factory(
        TcpingTestService,
        ip_address_service=ip_address_service,
        pubsub_service=pubsub_service,
        config_service=config_service,
        test_result_manager=test_result_manager,
        cache_service=cache_service,
        provider_service=provider_service,
        enqueue_service=enqueue_service
    )
    
# 创建容器实例
container = ApplicationContainer()

# 辅助函数

def get_db_manager() -> DBManager:
    return container.db_manager()

async def get_redis_manager() -> RedisManager:
    return await container.redis_manager()

async def get_pubsub_service() -> PubSubService:
    return await container.pubsub_service()

async def get_provider_service() -> ProviderService:
    return await container.provider_service()

async def get_ip_range_service() -> IPRangeService:
    return await container.ip_range_service()

async def get_ip_address_service() -> IPAddressService:
    return await container.ip_address_service()

async def get_enqueue_service() -> EnqueueService:
    return container.enqueue_service()

def get_config_service() -> ConfigService:
    return container.config_service()

async def get_tcping_test_service() -> TcpingTestService:
    return await container.tcping_test_service()