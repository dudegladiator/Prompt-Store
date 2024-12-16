import json
from datetime import datetime
from typing import Any, Optional, Callable
from functools import wraps
import hashlib
import redis
from fastapi import Request
from utils.config import settings
from utils.app_logger import setup_logger
from app import redis_client_main

logger = setup_logger("utils/redis_cache.py")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class RedisCache:
    def __init__(self):
        self.redis_client = redis_client_main
        try:
            self.redis_client.ping()
            logger.info("Successfully connected to Redis Cache")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis Cache connection error: {e}")
            raise

    async def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    return None
            return None
        except redis.RedisError as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        try:
            return self.redis_client.setex(
                name=key,
                time=expire,
                value=json.dumps(value, cls=DateTimeEncoder)
            )
        except redis.RedisError as e:
            logger.error(f"Redis set error: {e}")
            return False

def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    params = {
        'args': args,
        'kwargs': {k: v for k, v in kwargs.items() if k != 'request'}
    }
    param_str = json.dumps(params, sort_keys=True)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    return f"cache:{func_name}:{param_hash}"

def cached(expire: int = 300):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = RedisCache()
            cache_key = generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get cached response
            cached_response = await cache.get(cache_key)
            
            if cached_response is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_response  # Already decoded JSON

            # Execute function if cache miss
            response = await func(*args, **kwargs)
            
            # Cache the response
            await cache.set(cache_key, response, expire)
            logger.debug(f"Cache set for key: {cache_key}")
            
            return response
        return wrapper
    return decorator