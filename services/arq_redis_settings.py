import os
from typing import Optional, List, Tuple, Union
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
from arq.connections import Retry

@dataclass
class CustomRedisSettings:
    """
    Custom class to hold redis connection settings.
    """

    host: Union[str, List[Tuple[str, int]]] = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', 6379))
    unix_socket_path: Optional[str] = None
    database: int = int(os.getenv('REDIS_DB', 0))
    username: Optional[str] = os.getenv('REDIS_USERNAME')
    password: Optional[str] = os.getenv('REDIS_PASSWORD')
    ssl: bool = bool(os.getenv('REDIS_SSL', False))
    ssl_keyfile: Optional[str] = os.getenv('REDIS_SSL_KEYFILE')
    ssl_certfile: Optional[str] = os.getenv('REDIS_SSL_CERTFILE')
    ssl_cert_reqs: str = os.getenv('REDIS_SSL_CERT_REQS', 'required')
    ssl_ca_certs: Optional[str] = os.getenv('REDIS_SSL_CA_CERTS')
    ssl_ca_data: Optional[str] = os.getenv('REDIS_SSL_CA_DATA')
    ssl_check_hostname: bool = bool(os.getenv('REDIS_SSL_CHECK_HOSTNAME', False))
    conn_timeout: int = int(os.getenv('REDIS_CONN_TIMEOUT', 1))
    conn_retries: int = int(os.getenv('REDIS_CONN_RETRIES', 5))
    conn_retry_delay: int = int(os.getenv('REDIS_CONN_RETRY_DELAY', 1))
    max_connections: Optional[int] = int(os.getenv('REDIS_MAX_CONNECTIONS')) if os.getenv('REDIS_MAX_CONNECTIONS') else None

    sentinel: bool = bool(os.getenv('REDIS_SENTINEL', False))
    sentinel_master: str = os.getenv('REDIS_SENTINEL_MASTER', 'mymaster')

    retry_on_timeout: bool = bool(os.getenv('REDIS_RETRY_ON_TIMEOUT', False))
    retry_on_error: Optional[List[Exception]] = None
    retry: Optional[Retry] = None

    @classmethod
    def from_dsn(cls, dsn: str) -> 'CustomRedisSettings':
        conf = urlparse(dsn)
        if conf.scheme not in {'redis', 'rediss', 'unix'}:
            raise RuntimeError('invalid DSN scheme')
        query_db = parse_qs(conf.query).get('db')
        if query_db:
            # e.g. redis://localhost:6379?db=1
            database = int(query_db[0])
        elif conf.scheme != 'unix':
            database = int(conf.path.lstrip('/')) if conf.path else 0
        else:
            database = 0
        return CustomRedisSettings(
            host=conf.hostname,
            port=conf.port or 6379,
            ssl=conf.scheme == 'rediss',
            username=conf.username,
            password=conf.password,
            database=database,
            unix_socket_path=conf.path if conf.scheme == 'unix' else None,
        )