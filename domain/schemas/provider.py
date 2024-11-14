from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional, Dict, Any
import json
from services.logger import setup_logger

logger = setup_logger(__name__)

class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)  # name 不能为空，长度在 1 到 100 之间
    logo_url: Optional[str] = Field(None, max_length=255)  # logo_url 可以为空，最大长度为 255
    curl: Dict[str, Any] = Field(..., description="Curl configuration")  # curl 不能为空
    tcping: Dict[str, Any] = Field(..., description="Tcping configuration")  # tcping 不能为空
    monitor: Dict[str, Any] = Field(..., description="Monitor configuration")  # monitor 不能为空

    @model_validator(mode='before')
    @classmethod
    def validate_config(cls, values):
        for key in ['curl', 'tcping', 'monitor']:
            config = values.get(key)
            if config is not None and not isinstance(config, dict):
                try:
                    values[key] = json.loads(config)
                except json.JSONDecodeError as e:
                    logger.error(f"错误{e}")
                    raise ValueError(f"Invalid JSON format for {key}") from e
        return values

class ProviderUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None, min_length=1, max_length=100)  # name 可以为空，如果提供则长度在 1 到 100 之间
    logo_url: Optional[str] = Field(None, max_length=255)  # logo_url 可以为空，最大长度为 255
    curl: Optional[Dict[str, Any]] = Field(None, description="Curl configuration")  # curl 可以为空
    tcping: Optional[Dict[str, Any]] = Field(None, description="Tcping configuration")  # tcping 可以为空
    monitor: Optional[Dict[str, Any]] = Field(None, description="Monitor configuration")  # monitor 可以为空

    @model_validator(mode='before')
    @classmethod
    def validate_config(cls, values):
        for key in ['curl', 'tcping', 'monitor']:
            config = values.get(key)
            if config is not None and not isinstance(config, dict):
                try:
                    values[key] = json.loads(config)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format for {key}") from e
        return values

class Provider(BaseModel):
    id: int
    name: str
    logo_url: Optional[str]
    curl: Dict[str, Any]
    tcping: Dict[str, Any]
    monitor: Dict[str, Any]

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @model_validator(mode='after')
    def parse_config(self):
        for key in ['curl', 'tcping', 'monitor']:
            config = getattr(self, key)  # 直接访问实例的属性
            if config is not None and not isinstance(config, dict):
                try:
                    setattr(self, key, json.loads(config))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format for {key}") from e
        return self

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Provider':
        return cls(**data)

class ProviderResponse(Provider):
    pass

class ProviderCreateWithIPRanges(ProviderCreate):
    ip_ranges: List[str]