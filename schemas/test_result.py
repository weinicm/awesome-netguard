from datetime import datetime
import ipaddress
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from pydantic import Field

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

    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        ip = values.get("ip")
        if ip is None or not isinstance(ip, str) or not ipaddress.ip_address(ip).is_global:
            raise ValueError("ip must be a valid global IP address")        
        return values

class TcpingTestRequest(BaseModel):
    provider_id: Optional[int] = Field(None, description="The ID of the provider (optional)")
    ip_type: str = Field(..., description="The type of IP to test (required)")
    user_submitted_ips: Optional[List[str]] = Field(None, description="A list of user-submitted IPs (optional)")



class CurlTestRequest(BaseModel):
    provider_id: Optional[int] = Field(None, description="The ID of the provider (optional)")
    ip_type: str = Field(..., description="The type of IP to test (required)")
    user_submitted_ips: Optional[List[str]] = Field(None, description="A list of user-submitted IPs (optional)")
