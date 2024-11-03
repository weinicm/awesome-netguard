import logging
from typing import Optional
from attr import dataclass

# 设置日志配置
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class IPRange:
    start_ip: str  # 必需字段
    end_ip: str  # 必需字段
    provider_id: int  # 必需字段
    id: Optional[int] = None  # 可选字段
    cidr: Optional[str] = None  # 可选字段


    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'cidr': self.cidr,
            'start_ip': self.start_ip,
            'end_ip': self.end_ip,
            'provider_id': self.provider_id,
        }

    # @classmethod
    # def from_dict(cls, data: dict) -> 'IPRange':
    #     required_properties = {'start_ip', 'end_ip', 'provider_id'}
        
    #     # 确保所有必要的属性都存在
    #     for prop in required_properties:
    #         if prop not in data:
    #             raise ValueError(f"Missing property '{prop}'")

    #     # 获取 id 并允许其为 None
    #     id_value = data.get('id')

    #     # 检查 provider_id 是否为整数
    #     if not isinstance(data['provider_id'], int):
    #         raise ValueError("provider_id must be an integer")

    #     return cls(
    #         id=id_value,
    #         cidr=data.get('cidr'),
    #         start_ip=data['start_ip'],
    #         end_ip=data['end_ip'],
    #         provider_id=data['provider_id']
    #     )

    @classmethod
    def from_record(cls, record) -> 'IPRange':
        # 打印接收到的数据
        # logger.debug(f"Received data for IPRange: {record}")

        # 确保所有必要的属性都存在
        required_properties = {'start_ip', 'end_ip', 'provider_id'}

        # 检查所有必要的属性是否都存在
        for prop in required_properties:
            if prop not in record:
                logger.error(f"Missing property '{prop}' in record: {record}")
                raise ValueError(f"Missing property '{prop}'")

        # 提供默认值为 None 的可选字段
        id_value = record.get('id')
        if id_value is not None and not isinstance(id_value, int):
            logger.error(f"Property 'id' must be an integer or None in record: {record}")
            raise ValueError("Property 'id' must be an integer or None")

        cidr = record.get('cidr')

        start_ip = record.get('start_ip')
        if start_ip is None or not start_ip.strip():
            logger.error(f"Property 'start_ip' is None or empty in record: {record}")
            raise ValueError("Property 'start_ip' is None or empty")

        end_ip = record.get('end_ip')
        if end_ip is None or not end_ip.strip():
            logger.error(f"Property 'end_ip' is None or empty in record: {record}")
            raise ValueError("Property 'end_ip' is None or empty")

        provider_id = record.get('provider_id')
        if provider_id is None or not isinstance(provider_id, int):
            logger.error(f"Property 'provider_id' must be an integer in record: {record}")
            raise ValueError("Property 'provider_id' must be an integer")

        # 创建 IPRange 对象
        return cls(
            id=id_value,
            cidr=cidr,
            start_ip=start_ip,
            end_ip=end_ip,
            provider_id=provider_id
        )

    def __repr__(self):
        return (f"<IPRange(id={self.id}, cidr={self.cidr}, start_ip={self.start_ip}, "
                f"end_ip={self.end_ip}, provider_id={self.provider_id})>")