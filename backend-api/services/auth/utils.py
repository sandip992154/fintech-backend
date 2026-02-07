from datetime import datetime, timedelta
import re
import random
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt

from .constants import (
    PASSWORD_PATTERN,
    TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    OTP_LENGTH,
    OTP_EXPIRE_MINUTES,
    AUTH_ERRORS,
    ROLE_PREFIX_MAP
)
from config.config import get_settings
from services.models.models import User, OTP, Role, RefreshToken
from utils.gmail_utils import send_login_email

settings = get_settings()

def validate_password(password: str) -> bool:
    """Validate password against security requirements"""
    return bool(re.match(PASSWORD_PATTERN, password))

def generate_otp() -> str:
    """Generate a random OTP"""
    return str(random.randint(10 ** (OTP_LENGTH-1), (10 ** OTP_LENGTH) - 1))

def create_token_payload(user: User, role_name: str, permissions: list) -> Dict[str, Any]:
    """Create standardized token payload"""
    return {
        "sub": user.user_code,
        "role": role_name,
        "user_id": user.id,
        "permissions": permissions
    }

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def send_auth_email(user: User, password: Optional[str] = None, otp: Optional[str] = None) -> None:
    """Send authentication related emails"""
    try:
        await send_login_email(
            to_email=user.email,
            name=user.full_name,
            login_id=user.user_code,
            password=password,
            signup_link=None,
            role=user.role.name if hasattr(user.role, 'name') else None,
            otp=otp
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

def generate_user_code(db: Session, role: str) -> str:
    """Generate unique user code based on role"""
    prefix = ROLE_PREFIX_MAP.get(role, "BANDCUS")
    last_user = db.query(User).filter(User.user_code.like(f"{prefix}%")).order_by(User.id.desc()).first()
    
    last_num = 0
    if last_user and last_user.user_code:
        try:
            last_num = int(last_user.user_code.replace(prefix, ""))
        except ValueError:
            last_num = 0
    
    return f"{prefix}{last_num + 1:05d}"

def save_otp(db: Session, user_id: int) -> str:
    """Create and save new OTP"""
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    
    # Invalidate existing OTPs
    db.query(OTP).filter(OTP.user_id == user_id, OTP.is_used == False).update({"is_used": True})
    
    # Create new OTP
    otp_obj = OTP(
        user_id=user_id,
        otp_code=otp,
        expires_at=expires_at
    )
    db.add(otp_obj)
    db.commit()
    
    return otp

def verify_otp(db: Session, user_id: int, otp: str) -> bool:
    """Verify OTP validity"""
    otp_obj = db.query(OTP).filter(
        OTP.user_id == user_id,
        OTP.otp_code == otp,
        OTP.is_used == False,
        OTP.expires_at > datetime.utcnow()
    ).first()
    
    if not otp_obj:
        return False
    
    otp_obj.is_used = True
    db.commit()
    return True

def clear_refresh_tokens(db: Session, user_id: int) -> None:
    """Clear all refresh tokens for a user"""
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    db.commit()

def save_refresh_token(db: Session, token: str, user_id: int) -> None:
    """Save new refresh token"""
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        token=token,
        expires_at=expires_at,
        user_id=user_id
    )
    db.add(db_token)
    db.commit()