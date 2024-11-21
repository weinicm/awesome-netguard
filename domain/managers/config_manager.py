import json
from typing import Optional
from domain.schemas.config import Config, TcpingConfig  # 假设这些模型在 domain/schemas/config.py 文件中定义
from db.db_manager import DBManager
from services.logger import setup_logger

logger = setup_logger(__name__)

class ConfigManager:
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager
        self.system_config = None

    async def get_config_by_name(self, name: str) -> Optional[Config]:
        """
        根据名称获取配置。
        :param name: 配置名称
        :return: 配置对象，如果不存在则返回 None。
        """
        try:
            query = """
                SELECT * 
                FROM config
                WHERE name = $1;
            """
            result = await self.db_manager.fetchrow(query, name)
            if result:
                logger.info(f"获取到的配置数据是: {result}")
                config_data = {
                    'id': result['id'],
                    'name': result['name'],
                    'provider_id': result['provider_id'],
                    'curl': json.loads(result['curl']),
                    'tcping': json.loads(result['tcping']),
                    'nsi_option': json.loads(result['nsi_option']) if result['nsi_option'] else None,
                    'system_option': json.loads(result['system_option']),
                    'monitor': json.loads(result['monitor']),
                    'description': result['description'],
                }
                logger.info(f"config:{config_data}")
                return Config.from_dict(config_data)
            else:
                logger.warning(f"配置 {name} 未找到。")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"解析配置数据时发生错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取配置 {name} 时发生错误: {e}")
            return None

    async def get_config_by_provider_id(self, provider_id: int) -> Optional[Config]:
        """
        根据提供商 ID 获取配置。
        :param provider_id: 提供商 ID
        :return: 配置对象，如果不存在则返回 None。
        """
        try:
            query = """
                SELECT * 
                FROM config
                WHERE provider_id = $1;
            """
            result = await self.db_manager.fetchrow(query, provider_id)
            logger.info(f"获取到的配置数据是: {result['id']}")
            if result:
                config_data = {
                    'id': result['id'],
                    'name': result.get('name', 'fa'),   
                    'provider_id': result['provider_id'],
                    'curl': json.loads(result['curl']),
                    'tcping': json.loads(result['tcping']),
                    'monitor': json.loads(result['monitor']),
                    'description': result['description']
                }
                return Config.from_dict(config_data)
            else:
                logger.warning(f"配置未找到，提供商 ID: {provider_id}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"解析配置数据时发生错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取配置时发生错误: {e}")
            return None

    async def update_config(self, config: Config) -> Optional[Config]:
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
                return Config.from_dict(config_data)
            else:
                logger.error(f"配置更新失败，ID: {id}")
                return None
        except Exception as e:
            logger.error(f"配置更新失败，ID: {id}, 错误: {e}")
            return None
    async def delete_config(self, provider_id: int) -> bool:
        """
        删除提供商的配置。
        :param provider_id: 提供商 ID
        :return: 如果删除成功返回 True，否则返回 False。
        """
        try:
            query = "DELETE FROM config WHERE provider_id = $1;"
            await self.db_manager.execute(query, provider_id)
            logger.info(f"配置删除成功，提供商 ID: {provider_id}")
            return True
        except Exception as e:
            logger.error(f"配置删除失败，提供商 ID: {provider_id}, 错误: {e}")
            return False

    import json

    async def create_config(self, config: Config) -> Config:
        """
        创建新的配置。
        :param config: 新配置的对象
        :return: 如果创建成功返回 True，否则返回 False。
        """
        try:
            query = """
                INSERT INTO config (name, provider_id, curl, tcping, monitor, description)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, name, provider_id, curl, tcping, monitor, description;
            """
            # 将 CurlConfig 和 TcpingConfig 对象转换为 JSON 字符串
            curl_json = json.dumps(config.curl.model_dump())
            tcping_json = json.dumps(config.tcping.model_dump())
            monitor_json = json.dumps(config.monitor.model_dump())

            result = await self.db_manager.execute(
                query,
                config.name,
                config.provider_id,
                curl_json,
                tcping_json,
                monitor_json,
                config.description,
                fetch=True
            )
            if isinstance(result, list) and len(result) > 0:
                result = result[0]  # 假设结果是一个列表，取第一个元素

            logger.info(f"配置创建成功，名称: {config.name}, 提供商 ID: {config.provider_id}")
            config_data = {
                    'id': result['id'],
                    'name': result['name'],
                    'provider_id': result['provider_id'],
                    'curl': json.loads(result['curl']),
                    'tcping': json.loads(result['tcping']),
                    'monitor': json.loads(result['monitor']),
                    'description': result['description']
            }
            return Config.from_dict(config_data)
        except Exception as e:
            logger.error(f"配置创建失败，名称: {config.name}, 提供商 ID: {config.provider_id}, 错误: {e}")
            raise e

    async def config_exists(self, provider_id: int) -> bool:
        """
        检查配置是否存在。
        :param provider_id: 提供商 ID
        :return: 如果配置存在返回 True，否则返回 False。
        """
        try:
            query = "SELECT EXISTS(SELECT 1 FROM config WHERE provider_id = $1);"
            result = await self.db_manager.fetchrow(query, provider_id)
            logger.info(f"检查配置存在性，提供商 ID: {provider_id}, 结果: {result}")
            return result
        except Exception as e:
            logger.error(f"检查配置存在性时发生错误，提供商 ID: {provider_id}, 错误: {e}")
            return False
        
    async def get_provider_tcping_config(self,provider_id:int)->Optional[TcpingConfig]:
        try:
            query = "SELECT * FROM config WHERE provider_id = $1;"
            result = await self.db_manager.fetchrow(query, provider_id)
            if result:
                return TcpingConfig.from_dict(json.loads(result['tcping']))
            else:
                logger.warning(f"Configuration not found for provider ID: {provider_id}")
                return None
        except Exception as e:
            logger.error(f"Error fetching configuration for provider ID {provider_id}: {e}")
            return None