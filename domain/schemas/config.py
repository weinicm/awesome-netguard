from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Any, List, Optional, Dict, Union
import ipaddress
import json
from services.logger import setup_logger

logger = setup_logger(__name__)

# 定义 Config 模型
class Config(BaseModel):
    id: int = Field(..., gt=0)  # id 不能为空，且必须大于 0
    name: str = Field(..., min_length=1, max_length=100)  # name 不能为空，长度在 1 到 100 之间
    config_data: Dict[str, Any] = Field(..., description="Configuration data as JSONB")  # config_data 不能为空
    description: Optional[str] = Field(None, description="Description of the configuration")  # description 可以为空

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    @model_validator(mode='before')
    @classmethod
    def validate_config_data(cls, values):
        config_data = values.get('config_data')
        if config_data is not None and not isinstance(config_data, dict):
            try:
                values['config_data'] = json.loads(config_data)
            except json.JSONDecodeError as e:
                raise ValueError("config_data must be a valid JSON object") from e
        return values

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


# 配置更新模型
class ConfigUpdate(BaseModel):
    id: int = Field(..., gt=0)  # id 不能为空，且必须大于 0
    content: str  # content 是一个 JSON 字符串

    @field_validator('content')
    def validate_content(cls, v):
        try:
            # 尝试解析 content 字段为 JSON
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError("Content must be a valid JSON string") from e
        return v

    @model_validator(mode='before')
    @classmethod
    def parse_content(cls, values):
        content_str = values.get('content')
        if isinstance(content_str, str):
            try:
                content_dict = json.loads(content_str)
                values['content'] = content_dict
            except json.JSONDecodeError as e:
                raise ValueError("Content must be a valid JSON string") from e
        return values


# 配置更新提供商模型
class ConfigUpdateProviders(BaseModel):
    provider_ids: Optional[List[Union[int, str]]] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def validate_provider_ids(cls, values):
        provider_ids = values.get('provider_ids')
        if provider_ids is not None:
            for provider_id in provider_ids:
                if not isinstance(provider_id, (int, str)):
                    raise ValueError("provider_ids must contain only integers or strings")
        return values