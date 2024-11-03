from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict
import ipaddress
import json

# 配置更新模型
class ConfigUpdate(BaseModel):
    id: int = Field(..., gt=0)  # id 不能为空，且必须大于 0
    content: str  # content 是一个 JSON 字符串

    @field_validator('content')
    def validate_content(cls, v):
        try:
            # 尝试解析 content 字段为 JSON
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError("Content must be a valid JSON string") from e
        return v

# 创建提供者的请求体模型
class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)  # name 不能为空，长度在 1 到 100 之间
    api_url: Optional[str] = Field(None, max_length=255)  # api_url 可以为空，最大长度为 255
    config: Optional[str] = Field(None, description="Config can be a JSON string or null")  # config 可以为空或 JSON 字符串



# 更新提供者的请求体模型
class ProviderUpdate(BaseModel):
    id: int = Field(..., gt=0)  # id 不能为空，且必须大于 0
    name: str = Field(..., min_length=1, max_length=100)  # name 不能为空，长度在 1 到 100 之间
    api_url: Optional[str] = Field(None, max_length=255)  # api_url 可以为空，最大长度为 255
    config: Optional[str] = Field(None, description="Config can be a JSON string or null")  # config 可以为空或 JSON 字符串

    @field_validator('config')
    def validate_config(cls, v):
        if not v:
            raise ValueError("Config must not be empty")
        return v

# IP 范围输入模型
class StartEndIP(BaseModel):
    start_ip: Optional[str] = Field(None, description="Start IP address")
    end_ip: Optional[str] = Field(None, description="End IP address")

class IPRangeInput(BaseModel):
    provider_id: int =None
    data_format: Optional[str] = Field(None, description="Data format: 'cidrs', 'startip_endip', or 'single_ips'")
    cidrs: List[str] = Field(default_factory=list, description="List of CIDR ranges")
    startip_endip: List[StartEndIP] = Field(default_factory=list, description="List of start_ip and end_ip ranges")
    single_ips: List[str] = Field(default_factory=list, description="List of single IP addresses")

    # @model_validator(mode='after')
    # def validate_data(self) -> 'IPRangeInput':
    #     if self.data_format == 'cidrs' and self.cidrs:
    #         for ip_range in self.cidrs:
    #             if not self.is_valid_cidr(ip_range):
    #                 raise ValueError(f"Invalid CIDR range: {ip_range}")
    #     elif self.data_format == 'startip_endip' and self.startip_endip:
    #         for ip_range in self.startip_endip:
    #             if not self.is_valid_startip_endip(ip_range):
    #                 raise ValueError(f"Invalid start_ip-end_ip range: {ip_range}")
    #     elif self.data_format == 'single_ips' and self.single_ips:
    #         for ip_range in self.single_ips:
    #             if not self.is_valid_single_ip(ip_range):
    #                 raise ValueError(f"Invalid single IP: {ip_range}")
    #     return self

    # @staticmethod
    # def is_valid_cidr(ip_range: str) -> bool:
    #     try:
    #         ipaddress.ip_network(ip_range)
    #         return True
    #     except ValueError:
    #         return False

    # @staticmethod
    # def is_valid_startip_endip(ip_range: StartEndIP) -> bool:
    #     try:
    #         start_ip = ipaddress.ip_address(ip_range.start_ip)
    #         end_ip = ipaddress.ip_address(ip_range.end_ip)
    #         return True
    #     except ValueError:
    #         return False

    # @staticmethod
    # def is_valid_single_ip(ip_range: str) -> bool:
    #     try:
    #         ipaddress.ip_address(ip_range)
    #         return True
    #     except ValueError:
    #         return False
        


class TcpingTestRequest(BaseModel):
    provider_id: Optional[int] = Field(None, description="The ID of the provider (optional)")
    ip_type: str = Field(..., description="The type of IP to test (required)")
    user_submitted_ips: Optional[List[str]] = Field(None, description="A list of user-submitted IPs (optional)")