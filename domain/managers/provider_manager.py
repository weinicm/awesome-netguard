import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from domain.models.provider import Provider  # 假设 Provider 模型在 domain/models/provider.py 文件中定义
from db.dbmanager import DBManager
class ProviderManager:
    def __init__(self):
        self.db_manager = DBManager()

    async def get_providers(self) -> List[Provider]:
        query = "SELECT * FROM providers;"
        results = await self.db_manager.fetch(query)

        # 转换每个记录为 Provider 对象
        return [Provider.from_record(result) for result in results]

    async def get_provider_by_name(self, name: str) -> Optional[Provider]:
        query = "SELECT * FROM providers WHERE name = $1;"
        result = await self.db_manager.fetch(query, name)
        if result:
            return Provider.from_record(result[0])
        return None

    async def get_provider_by_id(self, provider_id: int) -> Optional[Provider]:
        query = "SELECT * FROM providers WHERE id = $1;"
        result = await self.db_manager.fetch(query, provider_id)
        if result:
            return Provider.from_record(result[0])
        return None

    async def create_provider(self, provider_dict: dict) -> Optional[Provider]:
        # 打印接收到的数据
        logging.debug(f"Received data for creating provider: {provider_dict}")

        # 提取数据
        name = provider_dict.get('name')
        api_url = provider_dict.get('api_url')
        config = provider_dict.get('config')
        logo_url = provider_dict.get('logo_url')

        # SQL 插入语句
        query = """
            INSERT INTO providers (name, api_url, config, logo_url)
            VALUES ($1, $2, $3, $4)
            RETURNING id, name, api_url, config, logo_url, created_at, updated_at;
        """

        # 执行插入并返回新创建的记录
        try:
            result = await self.db_manager.execute(query, name, api_url, config, logo_url, fetch=True)
            if result:
                logging.debug(f"Provider created successfully: {result}")
                return Provider.from_record(result[0])
            else:
                logging.error("Failed to create provider")
                return None
        except Exception as e:
            logging.error(f"Error creating provider: {e}")
            raise
    async def delete_provider(self, provider_id: int) -> bool:
        try:
            query = "DELETE FROM providers WHERE id = $1"
            await self.db_manager.execute(query, provider_id)
            return True
        except Exception as e:
            logging.error(f"Error deleting provider: {e}")
            return False
        

    async def update_provider(self, provider_id: int, provider_data: dict) -> Optional[Provider]:
        # 打印接收到的数据
        logging.debug(f"Received data for provider {provider_id}: {provider_data}")
        
        # 提取数据
        name = provider_data.get('name')
        api_url = provider_data.get('api_url')
        config = provider_data.get('config')
        logo_url = provider_data.get('logo_url')

        # SQL 更新语句
        query = """
            UPDATE providers
            SET name = $1, api_url = $2, config = $3, logo_url = $4, updated_at = NOW()
            WHERE id = $5
            RETURNING id, name, api_url, config, logo_url, created_at, updated_at;
        """

        # 执行更新并返回更新后的记录
        try:
            result = await self.db_manager.execute(query, name, api_url, config, logo_url, provider_id, fetch=True)
            if result:
                logging.debug(f"Provider {provider_id} updated successfully: {result}")
                return Provider.from_record(result[0])
            else:
                logging.error(f"Failed to update provider {provider_id}")
                return None
        except Exception as e:
            logging.error(f"Error updating provider: {e}")
            raise
    
    async def update_provider_fields(self, provider_id: int, provider_data: Dict[str, Any]) -> Optional[Provider]:
        """更新供应商的指定字段"""
        # 构建 SQL 更新语句
        set_clauses = []
        params = []

        for field, value in provider_data.items():
            set_clauses.append(f"{field} = ${len(params) + 1}")
            params.append(value)

        set_clauses_str = ', '.join(set_clauses)
        query = f"""
            UPDATE providers
            SET {set_clauses_str}, updated_at = NOW()
            WHERE id = ${len(params) + 1}
            RETURNING id, name, api_url, config, logo_url, created_at, updated_at;
        """

        # 添加 provider_id 到参数列表
        params.append(provider_id)

        # 执行更新并返回更新后的记录
        try:
            result = await self.db_manager.execute(query, *params, fetch=True)
            if result:
                logging.debug(f"Provider {provider_id} updated successfully: {result}")
                return Provider.from_record(result[0])
            else:
                logging.error(f"Failed to update provider {provider_id}")
                return None
        except Exception as e:
            logging.error(f"Error updating provider: {e}")
            raise

    async def get_provider_config(self, provider_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT config FROM providers WHERE id = $1;"
        result = await self.db_manager.fetch(query, provider_id)
        if result:
            return result[0]['config']
        return None

    async def update_config_by_name(
            self,
            provider_id: int,
            config_name: str,
            new_config: Dict[str, Any]
    ) -> None:
        """
        更新指定 provider 的 config 字段中的特定部分。
        
        :param provider_id: 要更新的 provider 的 ID。
        :param config_name: 配置名称（例如 'curl', 'tcping', 'monitor'）。
        :param new_config: 新的配置内容。
        """
        # 将新的配置转换为JSON字符串
        new_config_json = json.dumps(new_config)
        
        # 构建更新查询
        query = f"""
            UPDATE providers
            SET config = jsonb_set(config, '{{{config_name}}}', '{new_config_json}'::jsonb)
            WHERE id = $1;
        """
        logging.debug(f"Updating {query} configuration for provider with ID {provider_id}")
        # 执行更新
        await self.db_manager.execute(query, provider_id)

        logging.info(f"Updated {config_name} configuration for provider with ID {provider_id}")