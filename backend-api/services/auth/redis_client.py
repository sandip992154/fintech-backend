from typing import Optional
from redis import Redis
from config.config import get_settings

settings = get_settings()

_redis_client: Optional[Redis] = None

def get_redis_client() -> Redis:
    """Get or create Redis client singleton"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL,
            decode_responses=True  # Automatically decode responses to strings
        )
    
    return _redis_client

def close_redis_client() -> None:
    """Close Redis connection if open"""
    global _redis_client
    
    if _redis_client:
        _redis_client.close()
        _redis_client = None