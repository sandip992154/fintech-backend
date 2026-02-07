from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .token_service import TokenService
from .dependencies import get_token_service

class JWTBearerWithBlacklist(HTTPBearer):
    def __init__(self, auto_error: bool = True, verify_type: Optional[str] = None):
        super().__init__(auto_error=auto_error)
        self.verify_type = verify_type
        self.token_service: Optional[TokenService] = None

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        # Lazy load token service
        if not self.token_service:
            self.token_service = get_token_service()
            
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            if not self.auto_error:
                return None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token and check blacklist
        try:
            payload = self.token_service.verify_token(
                credentials.credentials,
                verify_type=self.verify_type
            )
            # Add token payload to request state for later use
            request.state.token_payload = payload
            return credentials
            
        except HTTPException as e:
            if not self.auto_error:
                return None
            raise e
        except Exception as e:
            if not self.auto_error:
                return None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )