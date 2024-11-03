from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional


# 创建提供者的请求体模型
class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)  # name 不能为空，长度在 1 到 100 之间
    api_url: Optional[str] = Field(None, max_length=255)  # api_url 可以为空，最大长度为 255
    config: Optional[str] = Field(None, description="Config can be a JSON string or null")  # config 可以为空或 JSON 字符串
    logo_url: Optional[str] = Field(None, description="The URL of the logo image") # 可以为空


class ProviderUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)  # name 不能为空，长度在 1 到 100 之间
    api_url: Optional[str] = Field(None, max_length=255)  # api_url 可以为空，最大长度为 255
    logo_url: Optional[str] = Field(None, description="The URL of the logo image") # 可以为空


class ProviderUpdateTcping(BaseModel):
    port: int | None = Field(default=None)
    enable: bool | None = Field(default=None)
    time_out: int | None = Field(default=None)
    avg_latency: float | None = Field(default=None)
    packet_loss: float | None = Field(default=None)
    std_deviation: float | None = Field(default=None)

    model_config = ConfigDict(validate_assignment=True)

    # 自定义验证器
    @classmethod
    def validate_fields(cls, values):
        non_none_fields = sum(1 for value in values.values() if value is not None)
        if non_none_fields == 0:
            raise ValueError("At least one field must be provided")
        return values

    # 使用 @model_validator 装饰器
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_field(cls, values):
        # 在模型验证之前进行全局验证
        validated_values = cls.validate_fields(values)
        return validated_values

class ProviderUpdateCurl(BaseModel):
    port: int | None = Field(default=None)
    speed: int | None = Field(default=None)
    enable: bool | None = Field(default=None)
    time_out: int | None = Field(default=None)
    download_url: str | None = Field(default=None)

    model_config = ConfigDict(validate_assignment=True)

    # 自定义验证器
    @classmethod
    def validate_fields(cls, values):
        non_none_fields = sum(1 for value in values.values() if value is not None)
        if non_none_fields == 0:
            raise ValueError("At least one field must be provided")
        return values

    # 使用 @model_validator 装饰器
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_field(cls, values):
        # 在模型验证之前进行全局验证
        validated_values = cls.validate_fields(values)
        return validated_values


class ProviderUpdateMonitor(BaseModel):
    count: int | None = Field(default=None)
    auto_fill: bool | None = Field(default=None)
    min_count: int | None = Field(default=None)
    auto_delete: bool | None = Field(default=None)
    download_test_number: int | None = Field(default=None)

    model_config = ConfigDict(validate_assignment=True)

    # 自定义验证器
    @classmethod
    def validate_fields(cls, values):
        non_none_fields = sum(1 for value in values.values() if value is not None)
        if non_none_fields == 0:
            raise ValueError("At least one field must be provided")
        return values

    # 使用 @model_validator 装饰器
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_field(cls, values):
        # 在模型验证之前进行全局验证
        validated_values = cls.validate_fields(values)
        return validated_values






