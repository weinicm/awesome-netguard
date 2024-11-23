import os
import redis

try:
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    print(f"Connecting to Redis at host: {redis_host}, port: {redis_port}")
    r = redis.Redis(host=redis_host, port=redis_port)
    result = r.ping()
    print(f"Ping result: {result}")
except Exception as e:
    print(f"Exception: {e}")
