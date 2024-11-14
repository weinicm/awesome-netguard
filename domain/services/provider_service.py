from typing import Optional, List
from domain.managers.provider_manager import ProviderManager
from domain.schemas.provider import ProviderCreate, ProviderUpdate
from services.pubsub_service import PubSubService
from domain.schemas.provider import Provider
import logging

logger = logging.getLogger(__name__)


class ProviderService:
    def __init__(self, provider_manager: ProviderManager, pubsub_service: PubSubService):
        self.provider_manager = provider_manager
        self.pubsub_service = pubsub_service

    async def create_provider(self, provider_create: ProviderCreate) -> Provider:
        """
        创建新的提供者。

        :param provider_create: ProviderCreate 模型
        :return: 创建的 Provider 实例
        """
        # 将 ProviderCreate 模型转换为字典
        provider_data = provider_create.model_dump()

        # 调用 provider_manager.create 方法，传递字典
        provider = await self.provider_manager.create(provider_data)
        if provider:
            return provider
        else:
            logger.error(f"Failed to create provider {provider_create.name}.")
            return None
    

    async def get_provider_by_id(self, provider_id: int) -> Optional[Provider]:
        """
        根据提供商 ID 获取 Provider 实例。

        :param provider_id: 提供商的唯一标识符
        :return: Provider 实例，如果找不到则返回 None
        """
        provider_data =await self.provider_manager.get_provider_by_id(provider_id)
        if provider_data:
            return Provider.from_dict(provider_data.to_dict())
        return None

    async def update_provider(self, provider_id: int, provider_update: ProviderUpdate) -> Optional[Provider]:
        """
        更新提供商的配置信息。

        :param provider_id: 提供商的唯一标识符
        :param provider_update: ProviderUpdate 模型
        :return: 更新后的 Provider 实例，如果失败则返回 None
        """
        provider =await self.get_provider_by_id(provider_id)
        if provider:
            try:
                if provider_update.name is not None:
                    provider.name = provider_update.name
                provider.logo_url = provider_update.logo_url
                if provider_update.curl is not None:
                    provider.curl.update(provider_update.curl)
                if provider_update.tcping is not None:
                    provider.tcping.update(provider_update.tcping)
                if provider_update.monitor is not None:    
                    provider.monitor.update(provider_update.monitor)
                await self.provider_manager.update_provider(provider)
                logger.info(f"Provider {provider_id} updated successfully.")
                return provider
            except AttributeError as e:
                logger.error(f"Attribute error: {e}")
        logger.warning(f"Failed to update provider {provider_id}.")
        return None


    async def get_all_providers(self) -> List[Provider]:
        """
        获取所有未删除的提供者。

        :return: Provider 实例列表
        """
        providers= await self.provider_manager.get_all_providers()
        return providers

    async def get_deleted_providers(self) -> List[Provider]:
        """
        获取所有已删除的提供者。

        :return: Provider 实例列表
        """
        providers_data =await self.provider_manager.get_deleted_providers()
        providers = [Provider.from_dict(provider_data.to_dict()) for provider_data in providers_data]
        return providers
    
    async def delete_provider(self, provider_id: int) -> bool:
        """
        删除指定 ID 的提供者。

        :param provider_id: 提供商的唯一标识符
        :return: 删除成功返回 True，否则返回 False
        """
        deleted =await self.provider_manager.delete_provider(provider_id)
        if deleted:
            logger.info(f"Provider {provider_id} deleted successfully.")
            return True
        else:
            logger.error(f"Failed to delete provider {provider_id}.")
            return False
        
    async def hard_delete_provider(self, provider_id: int) -> bool:
        """
        彻底删除指定 ID 的提供者。

        :param provider_id: 提供商的唯一标识符
        :return: 彻底删除成功返回 True，否则返回 False
        """
        hard_deleted =await self.provider_manager.hard_delete_provider(provider_id)
        if hard_deleted:
            logger.info(f"Provider {provider_id} permanently deleted.")
            return True
