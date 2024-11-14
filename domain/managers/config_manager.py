import json
import logging
from typing import List, Optional
from domain.schemas.config import Config  # 假设 Config 模型在 domain/models/config.py 文件中定义
from db.db_manager import DBManager

class ConfigManager:
    def __init__(self):
        self.db_manager = DBManager()
        self.system_config = None
        
    
    async def get_config_by_name(self, name: str) -> Optional[Config]:
        query = "SELECT id, name, config_data FROM config WHERE name = $1;"
        result = await self.db_manager.fetch(query, name)
        if result:
            return Config.from_dict(result[0])
        return None

    async def update_config(self, id: int, content: str):
        query = """
            UPDATE config
            SET config_data = $1
            WHERE id = $2;
        """
        try:
            # 执行更新查询，不获取返回值
            await self.db_manager.execute(query, content, id, fetch=False)
        except Exception as e:
            # 如果在处理过程中发生任何异常，记录错误并抛出异常
            logging.error(f"Error updating config with id: {id}", exc_info=True)
            raise

    async def get_all_configs(self) -> List[Config]:
        query = "SELECT id, name, config_data FROM config;"
        results = await self.db_manager.fetch(query)
        return [Config.from_dict(result) for result in results]
    

    async def update_provider_list(self, data):
        name = "monitor_option"
        try:
            query = """
                    UPDATE config
                    SET config_data = jsonb_set(
                        config_data::jsonb,
                        '{providers}',
                        $1::jsonb, 
                        True 
                    )
                    WHERE name = $2
                """
            await self.db_manager.execute(query, json.dumps(data), name)
        except Exception as e:
            logging.error(f"Error updating provider list: {e}")
            raise 
    
    