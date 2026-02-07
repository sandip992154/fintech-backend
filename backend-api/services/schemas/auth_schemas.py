from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    base_url: Optional[str] = None
    
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

class PasswordResetResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str
    code: str
    success: bool = False