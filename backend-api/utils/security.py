from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, List, Union
import re
from utils.logging_config import get_logger
from config.config import settings

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Union[str, datetime]]:
    """Verify a JWT token and return its payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class SecurityMiddleware:
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        exclude_paths: List[str] = None,
        rate_limit: int = 100,
        rate_limit_period: int = 60
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/health"]
        self.rate_limit = rate_limit
        self.rate_limit_period = rate_limit_period
        self.request_counts: Dict[str, List[float]] = {}

    async def __call__(self, request: Request, call_next):
        path = request.url.path
        
        # Skip security for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        try:
            # Rate limiting
            client_ip = request.client.host
            current_time = time.time()
            
            # Clean old requests
            if client_ip in self.request_counts:
                self.request_counts[client_ip] = [
                    t for t in self.request_counts[client_ip]
                    if current_time - t < self.rate_limit_period
                ]
            else:
                self.request_counts[client_ip] = []

            # Check rate limit
            if len(self.request_counts[client_ip]) >= self.rate_limit:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests"
                )

            # Add current request
            self.request_counts[client_ip].append(current_time)

            # Security headers
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            raise

class JWTBearer(HTTPBearer):
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        super(JWTBearer, self).__init__(auto_error=True)
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def __call__(self, request: Request) -> Optional[Dict]:
        try:
            credentials: HTTPAuthorizationCredentials = await super().__call__(request)
            
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authorization code"
                )

            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme"
                )

            decoded_token = self.verify_jwt(credentials.credentials)
            return decoded_token

        except JWTError as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials"
            )

    def verify_jwt(self, token: str) -> Dict:
        try:
            decoded_token = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return decoded_token
        except JWTError:
            raise

class RequestValidator:
    @staticmethod
    def validate_phone(phone: str) -> bool:
        pattern = r'^\+?[1-9]\d{9,14}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_aadhaar(aadhaar: str) -> bool:
        pattern = r'^\d{12}$'
        return bool(re.match(pattern, aadhaar))

    @staticmethod
    def validate_pan(pan: str) -> bool:
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
        return bool(re.match(pattern, pan))

    @staticmethod
    def validate_vehicle_number(vehicle_number: str) -> bool:
        pattern = r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$'
        return bool(re.match(pattern, vehicle_number))

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Remove potentially dangerous characters from input"""
        return re.sub(r'[<>&\'";}{}]', '', input_str)
