from db.dbmanager import DBManager
from domain.services.cache_service import CacheService
from domain.services.pubsub_service import PubSubService
from domain.services.queue_service import QueueService
from domain.services.redis_service import RedisManager
from domain.services.test_service import TestService
from domain.services.ip_address_service import IPAddressService
from domain.services.config_service import ConfigService
from domain.managers.test_result_manager import TestResultManager
from domain.services.provider_service import ProviderService

def get_db_manager():
    return DBManager()

def get_provider_service():
    return ProviderService()

def get_ip_address_service():
    return IPAddressService()

def get_config_service():
    return ConfigService()

def get_test_result_manager():
    return TestResultManager()

def get_cache_service():
    return CacheService(redis_manager=RedisManager())

def get_pubsub_service():
    return PubSubService.get_instance()

def get_queue_service():
    return QueueService.get_instance()

def get_test_service(
    provider_id: int,
    ip_address_service=get_ip_address_service(),
    pubsub_service=get_pubsub_service(),
    queue_service=get_queue_service(),
    config_service=get_config_service(),
    test_result_manager=get_test_result_manager(),
    cache_service=get_cache_service(),
    provider_service=get_provider_service()
):
    return TestService(
        ip_address_service=ip_address_service,
        pubsub_service=pubsub_service,
        queue_service=queue_service,
        config_service=config_service,
        test_result_manager=test_result_manager,
        cache_service=cache_service,
        provider_service = provider_service,
        provider_id=provider_id
    )