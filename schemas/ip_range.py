from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from typing import Dict, List
import ipaddress

class IPRangeCreate(BaseModel):
    cidrs: List[str] = Field(..., min_items=1, description="CIDR 列表，不能为空")
    provider_id: int = Field(..., description="供应商 ID，不能为空")

    @model_validator(mode='before')
    @classmethod
    def validate_cidrs(cls, values):
        cidrs = values.get('cidrs')
        if not cidrs:
            raise ValueError("CIDR 列表不能为空")
        for cidr in cidrs:
            try:
                # 使用 ip_interface 而不是 ip_network。因为ip_interface支持192.0.1.12/24，而ip_network不支持
                ipaddress.ip_interface(cidr)
            except ValueError as e:
                raise ValueError(f"无效的 CIDR: {cidr} - {e}")
        return values

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )
class IPRangeUpdateAPi(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    api_url: str = Field(None, max_length=255, description="API 地址")
    

class IPRangeUpdateCidrs(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    cidrs: List[str] = Field(default_factory=list, description="CIDR 列表")

    @model_validator(mode='before')
    @classmethod
    def validate_cidrs(cls, values):
        cidrs = values.get('cidrs', [])
        if cidrs:
            for cidr in cidrs:
                try:
                    # 使用 ip_interface 而不是 ip_network。因为 ip_interface 支持 192.0.1.12/24，而 ip_network 不支持
                    ipaddress.ip_interface(cidr)
                except ValueError as e:
                    raise ValueError(f"无效的 CIDR: {cidr} - {e}")
        return values

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )


class IPRangeUpdateIps(BaseModel):
    provider_id: int = Field(..., description="供应商 ID，不能为空")
    single_ips: List[str] = Field(default_factory=list, description="IP 地址列表")

    @model_validator(mode='before')
    @classmethod
    def validate_ips(cls, values):
        ips = values.get('single_ips', [])
        if ips:
            for ip in ips:
                try:
                    # 使用 ip_interface 而不是 ip_address，因为 ip_interface 支持带有掩码的地址
                    ipaddress.ip_interface(ip)
                except ValueError as e:
                    raise ValueError(f"无效的 IP 地址: {ip} - {e}")
        return values

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

class IPRangeUpdateCustomRange(BaseModel):
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
                    # 验证 start_ip
                    ipaddress.ip_interface(start_ip)
                except ValueError as e:
                    raise ValueError(f"无效的 start_ip: {start_ip} - {e}")

                try:
                    # 验证 end_ip
                    ipaddress.ip_interface(end_ip)
                except ValueError as e:
                    raise ValueError(f"无效的 end_ip: {end_ip} - {e}")
        return values

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )



# 示例用法
if __name__ == "__main__":
    try:
        # 创建有效的 IP 范围（包含 IPv4 和 IPv6）
        valid_ip_range = IPRangeUpdateCidrs(
            cidrs=["192.0.1.12/24", "10.0.0.0/8", "2001:db8::/32", "fe80::/64"],
            provider_id=1
        )
        print(valid_ip_range)

        # 创建无效的 IP 范围（包含无效的 CIDR）
        invalid_ip_range = IPRangeUpdateCidrs(
            cidrs=["192.0.1.12/33",  "2001:db8::/129"],
            provider_id=1
        )
    except ValidationError as e:
        # 打印详细的错误信息
        for error in e.errors():
            loc = error['loc']
            msg = error['msg']
            input_value = error['input']
            print(f"Validation error: {msg} (Field: {loc}, Value: {input_value})")