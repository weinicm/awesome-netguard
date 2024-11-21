import logging
from typing import Any, Dict, List, Optional
from db.db_manager import DBManager
from domain.schemas.monitor import Monitor
from pydantic import BaseModel

class MonitorManager:
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    async def create_monitor(self, create_monitor_data: dict) -> Monitor:
        """
        创建一个新的监控记录
        :param create_monitor_data: 创建监控记录的数据
        :return: 创建的监控记录
        """
        query = """
            INSERT INTO monitor (provider_id,  enable)
            VALUES ($1, $2)
            RETURNING id, provider_id,  enable
        """
        try:
            logging.debug(f"Executing query: {query} with args: {create_monitor_data}")
            result = await self.db_manager.fetchrow(query, create_monitor_data['provider_id'], create_monitor_data['enable'])
            return Monitor.from_dict(dict(result))
        except Exception as e:
            logging.error(f"Error creating monitor: {e}")
            raise

    async def update_monitor(self, monitor_id: int, update_monitor_data: dict) -> Monitor:
        """
        更新现有的监控记录
        :param monitor_id: 监控记录的 ID
        :param update_monitor_data: 更新监控记录的数据
        :return: 更新后的监控记录
        """
        query = """
            UPDATE monitor
            SET provider_id = $1, provider_name = $2, enable = $3
            WHERE id = $4
            RETURNING id, provider_id, provider_name, enable
        """
        try:
            logging.debug(f"Executing query: {query} with args: {update_monitor_data}, {monitor_id}")
            result = await self.db_manager.fetchrow(query, update_monitor_data.get('provider_id'), update_monitor_data.get('provider_name'), update_monitor_data.get('enable'), monitor_id)
            return Monitor.from_dict(BaseModel.model_dump(result))
        except Exception as e:
            logging.error(f"Error updating monitor: {e}")
            raise

    async def delete_monitor(self, monitor_id: int) -> bool:
        """
        删除监控记录
        :param monitor_id: 监控记录的 ID
        :return: 是否成功删除
        """
        query = """
            DELETE FROM monitor
            WHERE id = $1
            RETURNING id
        """
        try:
            logging.debug(f"Executing query: {query} with args: {monitor_id}")
            result = await self.db_manager.fetchrow(query, monitor_id)
            return result is not None
        except Exception as e:
            logging.error(f"Error deleting monitor: {e}")
            raise

    async def get_monitor(self, monitor_id: int) -> Monitor:
        """
        获取监控记录
        :param monitor_id: 监控记录的 ID
        :return: 监控记录
        """
        query = """
            SELECT id, provider_id, provider_name, enable
            FROM monitor
            WHERE id = $1
        """
        try:
            logging.debug(f"Executing query: {query} with args: {monitor_id}")
            result = await self.db_manager.fetchrow(query, monitor_id)
            return Monitor.from_dict(dict(result)) if result else None
        except Exception as e:
            logging.error(f"Error getting monitor: {e}")
            raise

    async def get_all_monitors(self) -> List[Monitor]:
        """
        获取所有监控记录
        :return: 所有监控记录的列表
        """
        query = """
            SELECT id, provider_id, provider_name, enable
            FROM monitor
        """
        try:
            logging.debug(f"Executing query: {query}")
            results = await self.db_manager.fetch(query)
            return [Monitor.from_dict(dict(result)) for result in results]
        except Exception as e:
            logging.error(f"Error getting all monitors: {e}")
            raise

    async def get_monitors_by_provider(self, provider_id: int) -> Optional[List[Monitor]]:
        """
        获取特定提供者的所有监控记录
        :param provider_id: 提供者的 ID
        :return: 特定提供者的所有监控记录的列表
        """
        query = """
            SELECT id, provider_id, enable
            FROM monitor
            WHERE provider_id = $1
        """
        try:
            results = await self.db_manager.fetchrow(query, provider_id)
            if results:
                return [Monitor.from_dict(results)]
            else:
                return None
        except Exception as e:
            logging.error(f"Error getting monitors by provider: {e}")
            raise

    async def enable_monitor(self, monitor_id: int) -> Monitor:
        """
        启用监控记录
        :param monitor_id: 监控记录的 ID
        :return: 启用后的监控记录
        """
        query = """
            UPDATE monitor
            SET enable = TRUE
            WHERE id = $1
            RETURNING id, provider_id, provider_name, enable
        """
        try:
            logging.debug(f"Executing query: {query} with args: {monitor_id}")
            result = await self.db_manager.fetchrow(query, monitor_id)
            return Monitor.from_dict(dict(result))
        except Exception as e:
            logging.error(f"Error enabling monitor: {e}")
            raise

    async def disable_monitor(self, monitor_id: int) -> Monitor:
        """
        停用监控记录
        :param monitor_id: 监控记录的 ID
        :return: 停用后的监控记录
        """
        query = """
            UPDATE monitor
            SET enable = FALSE
            WHERE id = $1
            RETURNING id, provider_id, provider_name, enable
        """
        try:
            logging.debug(f"Executing query: {query} with args: {monitor_id}")
            result = await self.db_manager.fetchrow(query, monitor_id)
            return Monitor.from_dict(dict(result))
        except Exception as e:
            logging.error(f"Error disabling monitor: {e}")
            raise