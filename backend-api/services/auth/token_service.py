from datetime import datetime, timedelta
import json
from typing import Optional, Union
from fastapi import HTTPException, status
from redis import Redis
from jose import jwt

from config.config import get_settings

settings = get_settings()

class TokenService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.blacklist_prefix = "token:blacklist:"
        self.token_info_prefix = "token:info:"
        self.access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM

    def create_access_token(self, data: dict) -> str:
        """Create a new access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + self.access_token_expires
        to_encode.update({"exp": expire, "type": "access"})
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        self._store_token_info(token, data.get("sub"), "access", expire)
        return token

    def create_refresh_token(self, data: dict) -> str:
        """Create a new refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + self.refresh_token_expires
        to_encode.update({"exp": expire, "type": "refresh"})
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        self._store_token_info(token, data.get("sub"), "refresh", expire)
        return token

    def blacklist_token(self, token: str) -> None:
        """Add a token to the blacklist"""
        try:
            # Decode token without verification to get expiration
            payload = jwt.get_unverified_claims(token)
            exp = payload.get("exp")
            
            if not exp:
                raise ValueError("Token has no expiration")
            
            # Store in Redis with TTL matching token expiration
            ttl = int(exp - datetime.utcnow().timestamp())
            if ttl > 0:
                self.redis.setex(
                    f"{self.blacklist_prefix}{token}",
                    ttl,
                    "revoked"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not blacklist token: {str(e)}"
            )

    def is_token_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted"""
        return bool(self.redis.get(f"{self.blacklist_prefix}{token}"))

    def _store_token_info(self, token: str, user_id: Union[str, int], token_type: str, expire: datetime) -> None:
        """Store token metadata in Redis"""
        token_info = {
            "user_id": str(user_id),
            "type": token_type,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expire.isoformat()
        }
        
        # Calculate TTL in seconds
        ttl = int((expire - datetime.utcnow()).total_seconds())
        if ttl > 0:
            self.redis.setex(
                f"{self.token_info_prefix}{token}",
                ttl,
                json.dumps(token_info)
            )

    def get_token_info(self, token: str) -> Optional[dict]:
        """Get stored token metadata"""
        info = self.redis.get(f"{self.token_info_prefix}{token}")
        if info:
            return json.loads(info)
        return None

    def revoke_all_user_tokens(self, user_id: Union[str, int]) -> None:
        """Revoke all tokens for a specific user"""
        pattern = f"{self.token_info_prefix}*"
        for key in self.redis.scan_iter(pattern):
            info = self.redis.get(key)
            if info:
                info_dict = json.loads(info)
                if info_dict.get("user_id") == str(user_id):
                    token = key.decode().replace(self.token_info_prefix, "")
                    self.blacklist_token(token)

    def verify_token(self, token: str, verify_type: Optional[str] = None) -> dict:
        """Verify a token and return its payload"""
        try:
            if self.is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if verify_type and payload.get("type") != verify_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {verify_type}"
                )
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token"
            )