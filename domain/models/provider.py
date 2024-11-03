import json
import logging
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List

# 设置日志配置
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class Provider:
    id: int  # 必需字段
    name: str  # 必需字段
    api_url: Optional[str] = None  # 可选字段
    config: Optional[Dict[str, Any]] = field(default_factory=dict)  # 可选字段，默认为空字典
    logo_url: Optional[str] = None  # 新增的 logo_url 字段
    ip_ranges: List[Dict[str, Any]] = field(default_factory=list)  # 关联的 IP 范围列表

    def to_dict(self) -> dict:
        # 将 Provider 对象转换为字典，便于与数据库兼容
        return asdict(self)

    @classmethod
    def from_record(cls, record) -> 'Provider':
        # 打印接收到的数据
        # logger.debug(f"Received data for Provider: {record}")

        # 确保所有必要的属性都存在
        required_properties = {'id', 'name'}

        # 检查所有必要的属性是否都存在
        for prop in required_properties:
            if prop not in record:
                logger.error(f"Missing property '{prop}' in record: {record}")
                raise ValueError(f"Missing property '{prop}'")

        # 提供默认值为 None 的可选字段
        id_value = record.get('id')
        if id_value is None:
            logger.error(f"Property 'id' is None in record: {record}")
            raise ValueError("Property 'id' is None")

        name = record.get('name')
        if name is None or not name.strip():
            logger.error(f"Property 'name' is None or empty in record: {record}")
            raise ValueError("Property 'name' is None or empty")

        api_url = record.get('api_url')
        config = record.get('config')
        logo_url = record.get('logo_url')  # 获取新增的 logo_url 字段
        ip_ranges = record.get('ip_ranges', [])  # 获取关联的 IP 范围列表

        # 如果 config 是字符串，则尝试将其解析为 JSON
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                logger.error("Invalid JSON format for config")
                raise ValueError("Invalid JSON format for config")

        # 创建 Provider 对象
        return cls(
            id=id_value,
            name=name,
            api_url=api_url,
            config=config,
            logo_url=logo_url,
            ip_ranges=ip_ranges
        )
    
    

    def __repr__(self):
        return (f"<Provider(id={self.id}, name={self.name}, "
                f"api_url={self.api_url}, config={self.config}, "
                f"logo_url={self.logo_url}, ip_ranges={self.ip_ranges})>")  # 更新 repr 方法以包含 ip_ranges