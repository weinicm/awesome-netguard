from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional, Dict, Any
import json
from services.logger import setup_logger

logger = setup_logger(__name__)

class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)  # name 不能为空，长度在 1 到 100 之间
    logo_url: Optional[str] = Field(None, max_length=255)  # logo_url 可以为空，最大长度为 255

class ProviderUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None, min_length=1, max_length=100)  # name 可以为空，如果提供则长度在 1 到 100 之间
    logo_url: Optional[str] = Field(None, max_length=255)  # logo_url 可以为空，最大长度为 255

class Provider(BaseModel):
    id: int
    name: str
    logo_url: Optional[str]

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Provider':
        return cls(**data)

class ProviderResponse(Provider):
    pass

class ProviderCreateWithIPRanges(ProviderCreate):
    ip_ranges: List[str]