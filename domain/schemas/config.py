from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Any, List, Optional, Dict, Union

# 定义嵌套模型
class CurlConfig(BaseModel):
    port: int
    speed: int
    enable: bool
    time_out: int
    download_url: str
    ip_v4_enable: bool
    ip_v6_enable: bool
    count: int

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    @classmethod
    def from_record(cls, record):
        return cls(
            port=record['port'],
            speed=record['speed'],
            enable=record['enable'],
            time_out=record['time_out'],
            download_url=record['download_url'],
            ip_v4_enable=record['ip_v4_enable'],
            ip_v6_enable=record['ip_v6_enable'],
            count=record['count']
        )

class TcpingConfig(BaseModel):
    port: int
    enable: bool
    time_out: int
    avg_latency: int
    packet_loss: float
    ip_v4_enable: bool
    ip_v6_enable: bool
    std_deviation: str
    count:int

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    
class MonitorConfig(BaseModel):
    count: int
    auto_fill: bool
    min_count: int
    providers: List[int]
    auto_delete: bool
    download_test_number: int

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

# 定义 Config 模型
class Config(BaseModel):
    id: int = Field(..., gt=0)
    name: Optional[str] = Field('', min_length=1, max_length=100)
    provider_id: int
    curl: CurlConfig
    tcping: TcpingConfig
    monitor: MonitorConfig
    description: Optional[str] = Field('', description="Description of the configuration")

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'provider_id': self.provider_id,
            'curl': self.curl.model_dump(),
            'tcping': self.tcping.model_dump(),
            'monitor': self.monitor.model_dump(),
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            provider_id=data.get('provider_id', 0),
            curl=CurlConfig(**data.get('curl', {})),
            tcping=TcpingConfig(**data.get('tcping', {})),
            monitor=MonitorConfig(**data.get('monitor', {})),
            description=data.get('description')
        )

    def __repr__(self):
        return (f"<Config(id={self.id}, name={self.name}, provider_id={self.provider_id}, "
                f"curl={self.curl}, tcping={self.tcping}, "
                f"monitor={self.monitor}, description={self.description})>")

# 配置创建模型
class ConfigCreate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider_id: int
    curl: CurlConfig
    tcping: TcpingConfig
    monitor: MonitorConfig
    description: Optional[str] = Field(None, description="Description of the configuration")

    def to_config(self) -> Config:
        return Config(
            id=None,
            name=self.name,
            provider_id=self.provider_id,
            curl=self.curl,
            tcping=self.tcping,
            monitor=self.monitor,
            description=self.description
        )

# 配置更新模型
class ConfigUpdate(BaseModel):
    id: int = Field(..., gt=0)
    provider_id: int = Field(..., gt=0)
    content: dict

    @field_validator('content')
    def validate_content(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Content must be a valid dictionary")
        return v

    def apply_updates(self, config: Config):
        for key, value in self.content.items():
            if hasattr(config, key):
                attr = getattr(config, key)
                if isinstance(attr, BaseModel) and isinstance(value, dict):
                    attr.update(**value)
                else:
                    setattr(config, key, value)
        return config

# 默认配置模型
class DefualtConfig(BaseModel):
    curl: CurlConfig
    tcping: TcpingConfig
    monitor: MonitorConfig
    description: Optional[str] = Field(None, description="Description of the configuration")