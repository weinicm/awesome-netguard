from datetime import datetime
import ipaddress
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator, ValidationError

from services.logger import setup_logger

logger = setup_logger(__name__)

class TestResultCreate(BaseModel):
    ip: str
    avg_latency: Optional[float] = Field(None, description="Average latency")
    std_deviation: Optional[float] = Field(None, description="Standard deviation")
    packet_loss: Optional[float] = Field(None, description="Packet loss")
    download_speed: Optional[float] = Field(None, description="Download speed")
    is_locked: bool = Field(False, description="Is the result locked")
    status: Optional[str] = Field(None, description="Status of the test")
    test_type: Optional[str] = Field(None, description="Type of the test")
    test_time: Optional[datetime] = Field(None, description="Timestamp of the test")
    is_delete: bool = Field(False, description="Is the result deleted")

    @model_validator(mode='before')
    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        ip = values.get("ip")
        if ip is None or not isinstance(ip, str) or not ipaddress.ip_address(ip).is_global:
            raise ValueError("ip must be a valid global IP address")
        return values

class TestResult(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the test result")
    ip: str
    avg_latency: Optional[float] = Field(None, description="Average latency")
    std_deviation: Optional[float] = Field(None, description="Standard deviation")
    packet_loss: Optional[float] = Field(None, description="Packet loss")
    download_speed: Optional[float] = Field(None, description="Download speed")
    is_locked: bool = Field(False, description="Is the result locked")
    status: Optional[str] = Field(None, description="Status of the test")
    test_type: Optional[str] = Field(None, description="Type of the test")
    test_time: Optional[datetime] = Field(None, description="Timestamp of the test")
    is_delete: bool = Field(False, description="Is the result deleted")

    def to_dict(self) -> dict:
        # 将 TestResult 对象转换为字典，便于与数据库兼容
        return self.model_dump()

    @classmethod
    def from_record(cls, record) -> 'TestResult':
        # 确保所有必要的属性都存在
        required_properties = {'ip'}

        # 检查所有必要的属性是否都存在
        for prop in required_properties:
            if prop not in record:
                raise ValueError(f"Missing property '{prop}'")

        # 创建 TestResult 实例
        try:
            return cls(
                id=record.get('id'),
                ip=record['ip'],
                avg_latency=record.get('avg_latency'),
                std_deviation=record.get('std_deviation'),
                packet_loss=record.get('packet_loss'),
                download_speed=record.get('download_speed'),
                is_locked=record.get('is_locked', False),
                status=record.get('status'),
                test_type=record.get('test_type'),
                test_time=record.get('test_time'),
                is_delete=record.get('is_delete', False)
            )
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise

    def __repr__(self):
        return (f"<TestResult(id={self.id}, ip={self.ip}, "
                f"avg_latency={self.avg_latency}, std_deviation={self.std_deviation}, "
                f"packet_loss={self.packet_loss}, download_speed={self.download_speed}, "
                f"is_locked={self.is_locked}, status={self.status}, "
                f"test_type={self.test_type}, test_time={self.test_time}, "
                f"is_delete={self.is_delete})>")

class TestRequest(BaseModel):
    provider_id: Optional[int] = Field(None, description="The ID of the provider (optional)")
    user_submitted_ips: Optional[List[str]] = Field(None, description="A list of user-submitted IPs (optional)")

class CurlTestRequest(BaseModel):
    provider_id: Optional[int] = Field(None, description="The ID of the provider (optional)")
    user_submitted_ips: Optional[List[str]] = Field(None, description="A list of user-submitted IPs (optional)")

class BatchTestRequest(BaseModel):
    provider_ids: List[int] = Field(..., description="The IDs of the providers to test")