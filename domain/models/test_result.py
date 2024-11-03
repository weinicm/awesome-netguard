from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime

@dataclass
class TestResult:
    ip: str
    id: Optional[int] = None  # 可选字段
    avg_latency: Optional[float] = None  # 可选字段
    std_deviation: Optional[float] = None  # 可选字段
    packet_loss: Optional[float] = None  # 可选字段
    download_speed: Optional[float] = None  # 可选字段
    is_locked: bool = False  # 默认值为 False
    status: Optional[str] = None  # 可选字段
    test_type: Optional[str] = None  # 可选字段
    test_time: Optional[datetime] = None  # 新增字段
    is_delete: bool = False  # 默认值为 False

    def to_dict(self) -> dict:
        # 将 TestResult 对象转换为字典，便于与数据库兼容
        return asdict(self)

    @classmethod
    def from_record(cls, record) -> 'TestResult':
        # 确保所有必要的属性都存在
        required_properties = {'ip'}
        
        # 检查所有必要的属性是否都存在
        for prop in required_properties:
            if prop not in record:
                raise ValueError(f"Missing property '{prop}'")

        # 提供默认值为 None 或 False 的可选字段
        id_value = record.id
        ip = record.ip
        avg_latency = record.avg_latency
        std_deviation = record.std_deviation
        packet_loss = record.packet_loss
        download_speed = record.download_speed
        is_locked = record.is_locked
        status = record.status
        test_time = record.test_time
        test_type = record.test_type
        is_delete = record.is_delete

        return cls(
            id=id_value,
            ip=ip,
            avg_latency=avg_latency,
            std_deviation=std_deviation,
            packet_loss=packet_loss,
            download_speed=download_speed,
            is_locked=is_locked,
            status=status,
            test_time=test_time,
            test_type=test_type,
            is_delete=is_delete
        )

    def __repr__(self):
        return (f"<TestResult(id={self.id}, ip={self.ip}, "
                f"avg_latency={self.avg_latency}, std_deviation={self.std_deviation}, "
                f"packet_loss={self.packet_loss}, download_speed={self.download_speed}, "
                f"is_locked={self.is_locked}, status={self.status}, "
                f"test_type={self.test_type}, test_time={self.test_time}, "
                f"is_delete={self.is_delete})>")