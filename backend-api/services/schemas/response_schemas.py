from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime

class StandardResponse(BaseModel):
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class PaginatedResponse(BaseModel):
    """Paginated response format"""
    success: bool
    message: str
    data: List[Any]
    pagination: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class ErrorResponse(BaseModel):
    """Error response format"""
    success: bool = False
    message: str
    error: str
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class AuthResponse(BaseModel):
    """Authentication response format"""
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user_info: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)