from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class IPAddress:
    id: Optional[int] = None  # 可选字段
    ip_address: str = ''
    ip_type: str = ''
    provider_id: int = 0  # 现在 provider_id 是必需的

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'ip_type': self.ip_type,
            'provider_id': self.provider_id,
        }
    @classmethod
    def from_record(cls, record) -> 'IPAddress':
        required_properties = {'ip_address', 'ip_type', 'provider_id'}

        # 检查所有必要的属性是否都存在
        for prop in required_properties:
            if prop not in record:
                raise ValueError(f"Missing property '{prop}'")

        # 获取 id 并允许其为 None
        id_value = record.get('id')

        # 确保 provider_id 是一个整数
        if not isinstance(record['provider_id'], int):
            raise ValueError("provider_id must be an integer")

        return cls(
            id=id_value,
            ip_address=record['ip_address'],
            ip_type=record['ip_type'],
            provider_id=record['provider_id']
        )

    def __repr__(self):
        return (f"<IPAddress(id={self.id}, ip_address={self.ip_address}, ip_type={self.ip_type}, "
                f"provider_id={self.provider_id})>")

# 示例用法
if __name__ == "__main__":
    # 假设这是从数据库获取的记录
    record = {
        'id': 1,
        'ip_address': '192.168.1.1',
        'ip_type': 'IPv4',
        'provider_id': 123
    }

    ip_address = IPAddress.from_record(record)
    print(ip_address)