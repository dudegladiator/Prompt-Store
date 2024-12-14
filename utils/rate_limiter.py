from fastapi import HTTPException, Request
import redis
import time
from functools import wraps
from typing import Optional, Callable
from utils.config import settings
from utils.app_logger import setup_logger

logger = setup_logger("utils/rate_limiter.py")

class RateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URI)
        try:
            self.redis_client.ping()
            logger.info("Successfully connected to Redis")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            raise

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, Optional[int]]:
        """
        Simple rate limiting implementation using Redis
        """
        try:
            # Create a window key that includes the time window
            current_time = int(time.time())
            window_key = f"ratelimit:{key}:{current_time // window_seconds}"

            # Get the current count
            count = self.redis_client.get(window_key)
            
            if count is None:
                # First request in this window
                self.redis_client.setex(window_key, window_seconds, 1)
                return False, None
            
            count = int(count)
            if count >= max_requests:
                # Calculate retry after
                retry_after = window_seconds - (current_time % window_seconds)
                return True, retry_after
            
            # Increment the counter
            self.redis_client.incr(window_key)
            return False, None

        except redis.RedisError as e:
            logger.error(f"Redis error: {e}")
            return False, None  # Fail open in case of Redis errors

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Rate limiting decorator for FastAPI endpoints
    """
    def decorator(func):
        @wraps(func)
        async def wrapped(request: Request, *args, **kwargs):
            limiter = RateLimiter()
            
            # Get client IP
            client_ip = request.headers.get("X-Forwarded-For", request.client.host)
            
            # Add endpoint path to make rate limit specific to each endpoint
            rate_limit_key = f"{client_ip}:{request.url.path}"
            
            logger.debug(f"Checking rate limit for IP: {client_ip} on path: {request.url.path}")
            
            is_limited, retry_after = limiter.is_rate_limited(
                rate_limit_key,
                max_requests,
                window_seconds
            )
            
            if is_limited:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too many requests",
                        "retry_after": retry_after
                    }
                )
            
            return await func(request, *args, **kwargs)
        return wrapped
    return decorator