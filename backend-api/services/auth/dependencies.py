from functools import lru_cache
from fastapi import Depends
from .token_service import TokenService
from .redis_client import get_redis_client

@lru_cache()
def get_token_service() -> TokenService:
    """Get or create TokenService singleton"""
    return TokenService(get_redis_client())