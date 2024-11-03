import json
import logging
from typing import List, Optional
from domain.managers.config_manager import ConfigManager
from schemas1 import ConfigUpdate  # 假设 ConfigUpdate 在 schemas.py 文件中定义
from domain.models.config import Config  # 假设 Config 模型在 domain/models/config.py 文件中定义

class ConfigService:
    def __init__(self):
        self.config_manager = ConfigManager()

    async def get_config(self, name: str, default=None) -> Optional[Config]:
        try:
            # 从 ConfigManager 获取指定名称的配置
            result = await self.config_manager.get_config_by_name(name)
            if result is None:
                logging.error(f"Config with name {name} not found")
                return default
            return result
        except Exception as e:
            # 如果在处理过程中发生任何异常，记录错误并抛出异常
            logging.error(f"Error getting config with name: {name}", exc_info=True)
            raise

    async def update_config(self, config_data: ConfigUpdate):
        return await self.config_manager.update_config(config_data.id, json.dumps(config_data.content))

    async def get_all_configs(self) -> List[Config]:
        return await self.config_manager.get_all_configs()

    async def get_system_config(self) -> Optional[dict]:
        print("开始执行")
        # 调用 get_config 方法，传入 "system_option" 作为 name 参数
        result_str = await self.get_config(name="system_option")
        result = json.loads(result_str.config_data)
        return result if result else None

    async def get_curl_config(self) -> Optional[dict]:
        print("开始执行")
        # 调用 get_config 方法，传入 "system_option" 作为 name 参数
        result = await self.get_config(name="curl")
        config = json.loads(result.config_data)
        return config
    
    async def get_tcping_config(self) -> Optional[dict]:
        print("开始执行")
        # 调用 get_config 方法，传入 "system_option" 作为 name 参数
        result = await self.get_config(name="tcping")
        config = json.loads(result.config_data)
        return config
    
    async def get_monitor_config(self) -> Optional[dict]:
        print("开始执行")
        # 调用 get_config 方法，传入 "system_option" 作为 name 参数
        result_str = await self.get_config(name="monitor_option")
        result = json.loads(result_str.config_data)
        return result if result else None
    
    async def get_monitor_list(self) -> Optional[dict]:
        retult = await self.get_config(name="monitor_option")
        if retult:
            retult = json.loads(retult.config_data)
            logging.info(retult)
        return retult.get("providers")
    
    async def update_monitor_list(self, data):
        await self.config_manager.update_provider_list(data)