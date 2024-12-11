from fastapi import HTTPException, Request
import redis
from datetime import datetime
import time
from functools import wraps
from typing import Optional
from utils.config import settings

class RateLimiter:
    def __init__(self):
        self.redis_client = redis.from_StrictRedis.from_url(settings.REDIS_URI)
        
    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Optional[int]]:
        """
        Check if the request should be rate limited
        Returns: (is_limited, retry_after_seconds)
        """
        current = int(time.time())
        window_key = f"{key}:{current // window_seconds}"
        
        try:
            # Increment the counter for the current window
            requests = self.redis_client.incr(window_key)
            
            # Set expiration if this is the first request in the window
            if requests == 1:
                self.redis_client.expire(window_key, window_seconds)
            
            if requests > max_requests:
                retry_after = window_seconds - (current % window_seconds)
                return True, retry_after
                
            return False, None
            
        except redis.RedisError:
            # If Redis is unavailable, fail open (allow the request)
            return False, None

def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    key_func=None
):
    """
    Rate limiting decorator that can be applied to API endpoints
    """
    def decorator(func):
        @wraps(func)
        async def wrapped(request: Request, *args, **kwargs):
            # Initialize rate limiter
            limiter = RateLimiter()
            
            # Generate rate limit key
            if key_func:
                rate_limit_key = key_func(request)
            else:
                # Default to IP-based rate limiting
                rate_limit_key = request.client.host
                
            is_limited, retry_after = await limiter.is_rate_limited(
                rate_limit_key,
                max_requests,
                window_seconds
            )
            
            if is_limited:
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