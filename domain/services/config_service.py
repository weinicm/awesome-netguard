import json
import logging
from typing import Optional
from domain.managers.config_manager import ConfigManager
from domain.schemas.config import Config, ConfigUpdate, ConfigCreate, TcpingConfig  # 假设 Config、ConfigUpdate 和 ConfigCreate 在 schemas.py 文件中定义

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, config_manager: ConfigManager ):
        self.config_manager = config_manager

    async def get_default_config(self) -> Optional[Config]:
        """
        获取默认配置。
        :return: 默认配置对象，如果不存在则返回 None。
        """
        try:
            default_config = await self.config_manager.get_config_by_name('default')
            if default_config:
                return default_config
            else:
                logger.warning("Default configuration not found.")
                return None
        except Exception as e:
            logger.error(f"Error fetching default configuration: {e}")
            return None

    async def get_config_by_provider(self, provider_id: int) -> Config:
        """
        根据提供商 ID 获取配置。
        :param provider_id: 提供商 ID
        :return: 配置对象，如果不存在则返回 None。
        """
        try:
            config = await self.config_manager.get_config_by_provider_id(provider_id)
            logger.info(f"Configuration found for provider ID: {config}")
            if config:
                return config
            else:
                logger.warning(f"Configuration not found for provider ID: {provider_id}")
                return None
        except Exception as e:
            logger.error(f"Error fetching configuration for provider ID {provider_id}: {e}")
            return None


        """
        更新配置。
        :param config: 更新的配置对象
        :return: 更新后的配置对象，如果失败则返回 None。
        """
        try:
            id = config.id
            query = """
                UPDATE config
                SET name = $1, curl = $2, tcping = $3, nsi_option = $4, system_option = $5, monitor = $6, description = $7
                WHERE id = $8
                RETURNING *;
            """
            result = await self.db_manager.fetchrow(
                query,
                config.name,
                json.dumps(config.curl.model_dump()),
                json.dumps(config.tcping.model_dump()),
                json.dumps(config.nsi_option.model_dump()) if config.nsi_option else None,
                json.dumps(config.system_option.model_dump()) if config.system_option else None,
                json.dumps(config.monitor.model_dump()),
                config.description,
                id
            )
            if result:
                logger.info(f"配置更新成功，ID: {id}")
                config_data = {
                    'id': result['id'],
                    'name': result['name'],
                    'provider_id': result['provider_id'],
                    'curl': json.loads(result['curl']),
                    'tcping': json.loads(result['tcping']),
                    'nsi_option': json.loads(result['nsi_option']) if result['nsi_option'] else None,
                    'system_option': json.loads(result['system_option']) if result['system_option'] else None,
                    'monitor': json.loads(result['monitor']),
                    'description': result['description']
                }
                return Config(**config_data)
            else:
                logger.error(f"配置更新失败，ID: {id}")
                return None
        except Exception as e:
            logger.error(f"配置更新失败，ID: {id}, 错误: {e}")
            return None
    async def delete_provider_config(self, provider_id: int) -> bool:
        """
        删除提供商的配置。
        :param provider_id: 提供商 ID
        :return: 如果删除成功返回 True，否则返回 False。
        """
        try:
            if not await self.config_manager.config_exists(provider_id):
                logger.warning(f"Configuration not found for provider ID: {provider_id}")
                return False

            await self.config_manager.delete_config(provider_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting configuration for provider ID {provider_id}: {e}")
            return False

    async def create_config(self, create_data: ConfigCreate) -> Optional[Config]:
        """
        创建新的提供商配置。
        :param create_data: 新配置的数据
        :return: 创建的配置对象，如果失败则返回 None。
        """
        try:
            await self.config_manager.delete_config(create_data.provider_id)
            return await self.config_manager.create_config(create_data)
        except Exception as e:
            logger.error(f"Error creating configuration: {e}")
            return None
        
    async def update_config(self, config: ConfigUpdate) -> Optional[Config]:
        """
        更新配置。
        :param config: 更新的配置对象
        :return: 更新后的配置对象，如果失败则返回 None。
        """
        try:
            return await self.config_manager.update_config(config)
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return None
        
    async def get_provider_tcping_config(self, provider_id: int) -> Optional[TcpingConfig]:
        try:
            config = await self.config_manager.get_provider_tcping_config(provider_id)
            if config:
                return config
            else:
                logger.warning(f"Configuration not found for provider ID: {provider_id}")
                return None
        except Exception as e:
            logger.error(f"Error fetching configuration for provider ID {provider_id}: {e}")
            return None
        
        