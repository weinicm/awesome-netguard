from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Union
import ipaddress
import json

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
    

class ConfigUpdateProviders(BaseModel):
    provider_ids: Optional[List[Union[int, str]]] = Field(default_factory=list)

   