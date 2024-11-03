import json
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    id: Optional[int] = None  # 可选字段
    name: str = ''
    config_data: Optional[str] = None  # 可选字段
    description: Optional[str] = None  # 可选字段

    def to_dict(self) -> dict:
        # 将 Config 对象转换为字典，便于与 JSONB 字段兼容
        return {
            'id': self.id,
            'name': self.name,
            'config_data': self.config_data,  # 可能是 None
            'description': self.description  # 可能是 None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        # 使用 dict.get 来获取可选字段，并设置默认值为 None 或空字符串
        return cls(
            id=data.get('id'),  # 可选字段
            name=data.get('name', ''),  # 必需字段，如果未提供则默认为空字符串
            config_data=data.get('config_data'),  # 可选字段
            description=data.get('description')  # 可选字段
        )

    def __repr__(self):
        return (f"<Config(id={self.id}, name={self.name}, "
                f"config_data={self.config_data}, description={self.description})>")