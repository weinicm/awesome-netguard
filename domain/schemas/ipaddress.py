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
    ip_type: str = Field(..., description="IP 类型，取值范围为 ipv4, ipv6")
    provider_id: Optional[int] = Field(None, description="供应商 ID")

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    def __repr__(self):
        return (f"<IPAddress(id={self.id}, ip_address={self.ip_address}, "
                f"ip_type={self.ip_type}, provider_id={self.provider_id})>")

    @classmethod
    def from_record(cls, record):
        """
        将 asyncpg 的 Record 对象转换为 IPAddress 对象
        """
        return cls(
            id=record['id'],
            ip_address=record['ip_address'],
            ip_type=record['ip_type'],
            provider_id=record['provider_id']
        )

    @model_validator(mode='before')
    @classmethod
    def validate_ip_type(cls, values):
        ip_type = values.get('ip_type')
        if ip_type not in [ip_type.value for ip_type in IPType]:
            raise ValueError(f"Invalid IP type '{ip_type}'. Valid types are: {', '.join([ip_type.value for ip_type in IPType])}")
        return values


    def __repr__(self):
        return (f"<IPAddress(id={self.id}, ip_address={self.ip_address}, "
                f"ip_type={self.ip_type.value}, provider_id={self.provider_id})>")