from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional
import ipaddress
import logging
from enum import Enum

# 设置日志配置
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class IPType(Enum):
    IPV4 = 'ipv4'
    IPV6 = 'ipv6'

class IPAddress(BaseModel):
    id: int = Field(..., description="ID，不能为空")
    ip_address: str = Field(..., description="IP 地址")
    ip_type: IPType = Field(..., description="IP 类型，取值范围为 ipv4, ipv6")
    provider_id: Optional[int] = Field(None, description="供应商 ID")

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @model_validator(mode='before')
    @classmethod
    def validate_fields(cls, values):
        # 验证 IP 地址
        try:
            ipaddress.ip_interface(values['ip_address'])
        except ValueError as e:
            raise ValueError(f"无效的 IP 地址: {values['ip_address']} - {e}")

        # 验证 IP 类型
        ip_type = values.get('ip_type')
        if not isinstance(ip_type, IPType):
            logger.error(f"Invalid IP type '{ip_type}'. Valid types are: {', '.join(t.value for t in IPType)}")
            raise ValueError(f"Invalid IP type '{ip_type}'. Valid types are: {', '.join(t.value for t in IPType)}")

        return values

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'ip_type': self.ip_type.value,  # 将枚举值转换为字符串
            'provider_id': self.provider_id
        }

    @classmethod
    def from_record(cls, record: dict) -> 'IPAddress':
        # 打印接收到的数据
        logger.debug(f"Received data for IPAddress: {record}")

        # 确保所有必要的属性都存在
        required_properties = {'ip_address', 'ip_type', 'id'}
        for prop in required_properties:
            if prop not in record:
                logger.error(f"Missing property '{prop}' in record: {record}")
                raise ValueError(f"Missing property '{prop}'")

        # 验证 id 字段
        id_value = record.get('id')
        if id_value is None or not isinstance(id_value, int):
            logger.error(f"Property 'id' must be an integer in record: {record}")
            raise ValueError("Property 'id' must be an integer")

        ip_address = record.get('ip_address')
        if ip_address is None or not ip_address.strip():
            logger.error(f"Property 'ip_address' is None or empty in record: {record}")
            raise ValueError("Property 'ip_address' is None or empty")

        ip_type = record.get('ip_type')
        try:
            ip_type = IPType(ip_type)
        except ValueError:
            logger.error(f"Invalid IP type '{ip_type}'. Valid types are: {', '.join(t.value for t in IPType)}")
            raise ValueError(f"Invalid IP type '{ip_type}'. Valid types are: {', '.join(t.value for t in IPType)}")

        provider_id = record.get('provider_id')
        if provider_id is not None and not isinstance(provider_id, int):
            logger.error(f"Property 'provider_id' must be an integer in record: {record}")
            raise ValueError("Property 'provider_id' must be an integer")

        # 创建 IPAddress 对象
        return cls(
            id=id_value,
            ip_address=ip_address,
            ip_type=ip_type,
            provider_id=provider_id
        )

    def __repr__(self):
        return (f"<IPAddress(id={self.id}, ip_address={self.ip_address}, "
                f"ip_type={self.ip_type.value}, provider_id={self.provider_id})>")