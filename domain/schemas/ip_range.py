from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Dict, List, Optional
import ipaddress
from enum import Enum, auto
import logging

# 设置日志配置
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class IPRangeSource(Enum):
    API = 'api'
    CUSTOM = 'custom'
    SINGLE = 'single'
    CIDRS = 'cidrs'

class IPRange(BaseModel):
    id: int = Field(..., description="ID，不能为空")
    start_ip: str = Field(..., description="起始 IP 地址")
    end_ip: str = Field(..., description="结束 IP 地址")
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    source: IPRangeSource = Field(..., description="来源，取值范围为 api, custom, single, cidrs")
    cidr: Optional[str] = Field(None, max_length=45, description="CIDR")

    @model_validator(mode='before')
    @classmethod
    def validate_fields(cls, values):
        # 验证 IP 地址
        try:
            ipaddress.ip_interface(values['start_ip'])
            ipaddress.ip_interface(values['end_ip'])
        except ValueError as e:
            raise ValueError(f"无效的 IP 地址: {values['start_ip']} 或 {values['end_ip']} - {e}")

        # 验证 source
        source = values.get('source')
        if not isinstance(source, IPRangeSource):
            logger.error(f"Invalid source '{source}'. Valid sources are: {', '.join(t.value for t in IPRangeSource)}")
            raise ValueError(f"Invalid source '{source}'. Valid sources are: {', '.join(t.value for t in IPRangeSource)}")

        return values

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'cidr': self.cidr,
            'start_ip': self.start_ip,
            'end_ip': self.end_ip,
            'provider_id': self.provider_id,
            'source': self.source.value  # 将枚举值转换为字符串
        }

    @classmethod
    def from_record(cls, record: dict) -> 'IPRange':
        # 打印接收到的数据
        logger.debug(f"Received data for IPRange: {record}")

        # 确保所有必要的属性都存在
        required_properties = {'start_ip', 'end_ip', 'provider_id', 'source', 'id'}
        for prop in required_properties:
            if prop not in record:
                logger.error(f"Missing property '{prop}' in record: {record}")
                raise ValueError(f"Missing property '{prop}'")

        # 验证 id 字段
        id_value = record.get('id')
        if id_value is None or not isinstance(id_value, int):
            logger.error(f"Property 'id' must be an integer in record: {record}")
            raise ValueError("Property 'id' must be an integer")

        cidr = record.get('cidr')

        start_ip = record.get('start_ip')
        if start_ip is None or not start_ip.strip():
            logger.error(f"Property 'start_ip' is None or empty in record: {record}")
            raise ValueError("Property 'start_ip' is None or empty")

        end_ip = record.get('end_ip')
        if end_ip is None or not end_ip.strip():
            logger.error(f"Property 'end_ip' is None or empty in record: {record}")
            raise ValueError("Property 'end_ip' is None or empty")

        provider_id = record.get('provider_id')
        if provider_id is None or not isinstance(provider_id, int):
            logger.error(f"Property 'provider_id' must be an integer in record: {record}")
            raise ValueError("Property 'provider_id' must be an integer")

        ip_source = record.get('source')
        try:
            ip_source = IPRangeSource(ip_source)
        except ValueError:
            logger.error(f"Invalid source '{ip_source}'. Valid sources are: {', '.join(t.value for t in IPRangeSource)}")
            raise ValueError(f"Invalid source '{ip_source}'. Valid sources are: {', '.join(t.value for t in IPRangeSource)}")

        # 创建 IPRange 对象
        return cls(
            id=id_value,
            cidr=cidr,
            start_ip=start_ip,
            end_ip=end_ip,
            provider_id=provider_id,
            source=ip_source
        )

    def __repr__(self):
        return (f"<IPRange(id={self.id}, cidr={self.cidr}, start_ip={self.start_ip}, "
                f"end_ip={self.end_ip}, provider_id={self.provider_id}, source={self.source.value})>")

# 其他模型保持不变
class IPRangeCreateFromAPI(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    api_url: str = Field(None, max_length=255, description="API 地址")

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

class IPRangeCreateFromCidrs(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    cidrs: List[str] = Field(default_factory=list, description="CIDR 列表")

    @model_validator(mode='before')
    @classmethod
    def validate_cidrs(cls, values):
        cidrs = values.get('cidrs', [])
        if cidrs:
            for cidr in cidrs:
                try:
                    ipaddress.ip_interface(cidr)
                except ValueError as e:
                    raise ValueError(f"无效的 CIDR: {cidr} - {e}")
        return values

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

class IPRangeCreateFromSingleIps(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    single_ips: List[str] = Field(default_factory=list, description="IP 地址列表")

    @model_validator(mode='before')
    @classmethod
    def validate_ips(cls, values):
        ips = values.get('single_ips', [])
        if ips:
            for ip in ips:
                try:
                    ipaddress.ip_interface(ip)
                except ValueError as e:
                    raise ValueError(f"无效的 IP 地址: {ip} - {e}")
        return values

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

class IPRangeCreateFromCustomRange(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    custom_ranges: List[Dict[str, str]] = Field(default_factory=list, description="自定义 IP 范围列表")

    @model_validator(mode='before')
    @classmethod
    def validate_custom_ranges(cls, values):
        custom_ranges = values.get('custom_ranges', [])
        if custom_ranges:
            for custom_range in custom_ranges:
                start_ip = custom_range.get('start_ip')
                end_ip = custom_range.get('end_ip')

                if not start_ip or not end_ip:
                    raise ValueError("每个自定义范围必须包含 start_ip 和 end_ip")

                try:
                    ipaddress.ip_interface(start_ip)
                except ValueError as e:
                    raise ValueError(f"无效的 start_ip: {start_ip} - {e}")

                try:
                    ipaddress.ip_interface(end_ip)
                except ValueError as e:
                    raise ValueError(f"无效的 end_ip: {end_ip} - {e}")
        return values

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

class IPRangeDelete(BaseModel):
    id: int = Field(..., description="ID，不能为空")

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

class IPRangeDeleteByApi(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    source: IPRangeSource = Field(default=IPRangeSource.API, description="IP 范围来源，不能为空")
    
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )
    

class IPRangeUpdateSingles(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    single_ips: List[str] = Field(default_factory=list, description="IP")
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

class IPRangeUpdateCidrs(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    cidrs: List[str]= Field(default_factory=list, description="CIDR 列表")
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )
class IPRangeUpdateCustomRange(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    custom_ranges: List[Dict[str, str]] = Field(default_factory=list, description="自定义 IP 范围列表")
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )   


class IPRangesByProviderResponse(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    api_range_list: List[IPRange] = Field(default_factory=list, description="API URL 列表")
    custom: List[IPRange] = Field(default_factory=list, description="自定义 IP 范围列表")
    single_ips: List[IPRange] = Field(default_factory=list, description="单个 IP 地址列表")
    cidrs: List[IPRange] = Field(default_factory=list, description="CIDR 列表")

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

class IPRangesBYProviderRequest(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )