import json
from typing import Any, Dict, List, Optional

from pydantic import ValidationError
from db.db_manager import DBManager
from domain.schemas.provider import Provider
from services.logger import setup_logger

logger = setup_logger(__name__)

class ProviderManager:
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    async def create(self, provider_dict: dict) -> Optional[Provider]:
        # 打印接收到的数据
        logger.debug(f"Received data for creating provider: {provider_dict}")

        # 构建 SQL 插入语句
        insert_query = """
        INSERT INTO public.providers (name, api_url, logo_url, deleted)
        VALUES ($1, $2, $3, $4)
        RETURNING id;
        """
        try:
            # 执行插入操作
            result = await self.db_manager.execute(
                insert_query,
                provider_dict['name'],
                provider_dict.get('api_url', ''),
                provider_dict.get('logo_url', None),
                False,
                fetch=True
            )
            if result:
                provider_id = result[0]['id']
                logger.info(f"Provider {provider_dict['name']} saved successfully with ID {provider_id}.")

                # 使用生成的 ID 和字典中的其他数据创建 Provider 实例
                provider_dict['id'] = provider_id
                provider = Provider(**provider_dict)
                return provider
            else:
                logger.error(f"Failed to save provider {provider_dict['name']}. No ID returned.")
                return None
        except Exception as e:
            logger.error(f"Failed to save provider {provider_dict['name']}: {e}")
            return None

    async def get_provider_by_id(self, provider_id: int) -> Optional[Provider]:
        """
        根据提供商 ID 获取 Provider 实例。

        :param provider_id: 提供商的唯一标识符
        :return: Provider 实例，如果找不到则返回 None
        """
        select_query = """
        SELECT * FROM public.providers WHERE id = $1 AND deleted = false;
        """
        try:
            provider_data = await self.db_manager.fetchrow(select_query, provider_id)
            provider_data = dict(provider_data)
            return Provider.from_dict(provider_data)
        except Exception as e:
            logger.error(f"Failed to get provider by ID {provider_id}: {e}")
            return None

    async def update_provider(self, provider: Provider) -> Optional[Provider]:
        """
        更新提供商的配置信息。

        :param provider: 提供商的实例
        :return: 更新后的 Provider 实例，如果失败则返回 None
        """
        id = provider.id
        existing_provider = await self.get_provider_by_id(id)
        logger.info(f"Existing provider: {existing_provider}")
        if existing_provider:
            try:
                # 更新 Provider 实例的属性
                existing_provider.name = provider.name
                existing_provider.logo_url = provider.logo_url

                # 构建 SQL 更新语句
                update_query = """
                UPDATE public.providers
                SET name = $1, logo_url = $2, updated_at = NOW()
                WHERE id = $3 AND deleted = false;
                """
                await self.db_manager.execute(update_query, existing_provider.name, existing_provider.logo_url, id)
                logger.info(f"Provider {id} updated successfully.")
                return existing_provider
            except Exception as e:
                logger.error(f"Failed to update provider {id}: {e}")
                logger.warning(f"Provider {id} not found or already deleted.")
                return None

    async def delete_provider(self, provider_id: int) -> bool:
        """
        逻辑删除提供商。

        :param provider_id: 提供商的唯一标识符
        :return: 删除成功返回 True，否则返回 False
        """
        delete_query = """
        UPDATE public.providers
        SET deleted = true, updated_at = NOW()
        WHERE id = $1 AND deleted = false;
        """
        logger.info(f"Deleting provider with query: {delete_query}")
        result = await self.db_manager.execute(delete_query, provider_id)
        if result == "UPDATE 1":
            logger.info(f"Provider {provider_id} deleted successfully.")
            return True
        else:
            logger.warning(f"Provider {provider_id} not found or already deleted.")
            return False

    async def hard_delete_provider(self, provider_id: int) -> bool:
        """
        彻底删除提供商。

        :param provider_id: 提供商的唯一标识符
        :return: 删除成功返回 True，否则返回 False
        """
        hard_delete_query = """
        DELETE FROM public.providers WHERE id = $1;
        """

        result = await self.db_manager.execute(hard_delete_query, provider_id)
        if result == "DELETE 1":
            logger.info(f"Provider {provider_id} hard deleted successfully.")
            return True
        else:
            logger.warning(f"Provider {provider_id} not found or already hard deleted.")
            return False

    async def get_all_providers(self) -> List[Provider]:
        """
        获取所有未删除的提供者。

        :return: Provider 实例列表
        """
        select_query = """
        SELECT * FROM public.providers WHERE deleted = false;
        """

        providers_data = await self.db_manager.fetch(select_query)
        providers = []

        for provider_data in providers_data:
            try:
                # 将 asyncpg.Record 转换为字典
                provider_data_dict = dict(provider_data)
                provider = Provider.from_dict(provider_data_dict)
                providers.append(provider)
            except ValidationError as e:
                logger.error(f"Validation error for provider data: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for provider data: {e}")

        return providers

    async def get_deleted_providers(self) -> List[Provider]:
        """
        获取所有已删除的提供者。

        :return: Provider 实例列表
        """
        select_query = """
        SELECT * FROM public.providers WHERE deleted = true;
        """

        providers_data = await self.db_manager.fetch(select_query)
        providers = [Provider.from_dict(dict(provider_data)) for provider_data in providers_data]
        return providers