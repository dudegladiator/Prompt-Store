import json
from typing import Any, Optional, Callable
from functools import wraps
import hashlib
import redis
from fastapi import Request
from utils.config import settings
from utils.app_logger import setup_logger

logger = setup_logger("utils/redis_cache.py")

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URI,
            decode_responses=True
        )
        try:
            self.redis_client.ping()
            logger.info("Successfully connected to Redis Cache")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis Cache connection error: {e}")
            raise

    async def get(self, key: str) -> Optional[str]:
        try:
            return self.redis_client.get(key)
        except redis.RedisError as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        try:
            return self.redis_client.setex(
                name=key,
                time=expire,
                value=json.dumps(value)
            )
        except redis.RedisError as e:
            logger.error(f"Redis set error: {e}")
            return False

def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a unique cache key based on function name and parameters
    """
    # Convert args and kwargs to a string representation
    params = {
        'args': args,
        'kwargs': {k: v for k, v in kwargs.items() if k != 'request'}  # Exclude request object
    }
    
    # Create a string representation of the parameters
    param_str = json.dumps(params, sort_keys=True)
    
    # Create a hash of the parameters
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    
    # Combine function name and parameter hash
    return f"cache:{func_name}:{param_hash}"

def cached(expire: int = 300):
    """
    Cache decorator that takes into account function parameters
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Initialize cache
            cache = RedisCache()
            
            # Generate unique cache key based on function name and parameters
            cache_key = generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get cached response
            cached_response = await cache.get(cache_key)
            
            if cached_response:
                logger.debug(f"Cache hit for key: {cache_key}")
                return json.loads(cached_response)

            # Execute function if cache miss
            response = await func(*args, **kwargs)
            
            # Cache the response
            await cache.set(cache_key, response, expire)
            logger.debug(f"Cache set for key: {cache_key}")
            
            return response
        return wrapper
    return decorator