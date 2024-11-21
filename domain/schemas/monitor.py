from pydantic import BaseModel, Field
from typing import Optional
import logging

# 设置日志配置
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Monitor(BaseModel):
    id: Optional[int] = Field(None, description="ID，自增主键")
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    enable: bool = Field(True, description="是否启用，默认为 True")

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'enable': self.enable
        }

    @classmethod
    def from_dict(cls, record: dict) -> 'Monitor':
        # 打印接收到的数据
        logger.debug(f"Received data for Monitor: {record}")

        # 确保所有必要的属性都存在
        required_properties = {'provider_id',  'enable'}
        for prop in required_properties:
            if prop not in record:
                logger.error(f"Missing property '{prop}' in record: {record}")
                raise ValueError(f"Missing property '{prop}'")

        # 验证 id 字段
        id_value = record.get('id')
        if id_value is not None and not isinstance(id_value, int):
            logger.error(f"Property 'id' must be an integer in record: {record}")
            raise ValueError("Property 'id' must be an integer")

        # 将 asyncpg 返回的记录转换为字典
        record_dict = dict(record)

        return cls(
            id=record_dict.get('id'),
            provider_id=record_dict['provider_id'],
            enable=record_dict['enable']
        )

class CreateMonitor(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    enable: bool = Field(True, description="是否启用，默认为 True")

    def to_dict(self) -> dict:
        return {
            'provider_id': self.provider_id,
            'enable': self.enable
        }

class UpdateMonitor(BaseModel):
    provider_id: Optional[int] = Field(None, description="供应商 ID，可以为空")
    enable: Optional[bool] = Field(None, description="是否启用，可以为空")

    def to_dict(self) -> dict:
        return {
            'provider_id': self.provider_id,
            'enable': self.enable
        }

class ResponseMonitor(BaseModel):
    id: int = Field(..., description="ID，自增主键")
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    enable: bool = Field(True, description="是否启用，默认为 True")

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'enable': self.enable
        }
        
