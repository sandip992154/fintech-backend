from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from typing import Optional
import logging

from database.database import get_db
from services.models.models import User
from services.models.password_reset import PasswordResetToken
from services.schemas.auth_schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    PasswordResetResponse,
    ErrorResponse
)
from services.auth.auth import get_password_hash
from utils.gmail_utils import send_reset_password_email

router = APIRouter(tags=["Password Reset"])
logger = logging.getLogger(__name__)

# Configuration
RESET_TOKEN_EXPIRE_HOURS = 24
MIN_PASSWORD_LENGTH = 8

def generate_reset_token() -> str:
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum requirements"""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    return True, ""

@router.post("/forgot-password", 
    response_model=PasswordResetResponse,
    responses={400: {"model": ErrorResponse}})
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
) -> PasswordResetResponse:
    """
    Send a password reset email to the user's registered email address.
    
    Parameters:
    - email: User's email address
    - base_url: Base URL for the reset password link (optional)
    """
    # Use provided base_url or default to the configured frontend URL
    base_url = request.base_url or "https://customer.bandarupay.pro"
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Return success even if user not found to prevent email enumeration
            return PasswordResetResponse(
                message="If a matching account was found, we've sent a password reset email."
            )

        # Generate reset token
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)

        # Save token to database
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.add(reset_token)
        
        # Send reset email
        reset_url = f"{base_url}/reset-password?token={token}"
        await send_reset_password_email(
            to_email=user.email,
            username=user.full_name,
            reset_link=reset_url
        )
        
        db.commit()
        
        return PasswordResetResponse(
            message="If a matching account was found, we've sent a password reset email."
        )
        
    except Exception as e:
        logger.error(f"Error in forgot_password: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )

@router.post("/reset-password",
    response_model=PasswordResetResponse,
    responses={400: {"model": ErrorResponse}})
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> PasswordResetResponse:
    """
    Reset user's password using the provided token.
    
    Parameters:
    - token: Reset token from email
    - new_password: New password
    - confirm_password: Confirmation of new password
    """
    try:
        # Validate passwords match
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
            
        # Validate password strength
        is_valid, error_message = validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )

        # Find valid reset token
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == request.token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()

        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Get user
        user = db.query(User).get(reset_token.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update password and mark token as used
        from services.auth.auth import get_password_hash
        user.hashed_password = get_password_hash(request.new_password)
        reset_token.is_used = True
        
        db.commit()
        
        return PasswordResetResponse(message="Password has been reset successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset_password: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, ""

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
) -> PasswordResetResponse:
    """
    Handle forgot password request and send reset email
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Don't reveal if email exists or not for security
            return PasswordResetResponse(
                message="If an account exists with this email, you will receive a password reset link",
                success=True
            )

        # Generate reset token
        reset_token = generate_reset_token()
        
        # Remove any existing unused tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).delete()
        
        # Create new reset token
        token_expires = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
        db_token = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=token_expires
        )
        db.add(db_token)
        db.commit()

        # Send reset email
        reset_link = f"{request.base_url}/reset-password?token={reset_token}"
        await send_reset_password_email(
            to_email=user.email,
            username=user.username,
            reset_link=reset_link
        )
        
        return PasswordResetResponse(
            message="If an account exists with this email, you will receive a password reset link",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error in forgot password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="An error occurred while processing your request",
                code="internal_error",
                success=False
            )
        )

@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> PasswordResetResponse:
    """
    Reset password using reset token
    """
    try:
        # Validate passwords match
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    detail="Passwords do not match",
                    code="password_mismatch",
                    success=False
                )
            )

        # Validate password strength
        is_valid, error_message = validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    detail=error_message,
                    code="weak_password",
                    success=False
                )
            )

        # Find valid reset token
        token_record = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == request.token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    detail="Invalid or expired reset token",
                    code="invalid_token",
                    success=False
                )
            )

        # Get user
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    detail="User not found",
                    code="user_not_found",
                    success=False
                )
            )

        # Update password
        user.hashed_password = get_password_hash(request.new_password)
        
        # Mark token as used
        token_record.is_used = True
        
        # Save changes
        db.commit()

        return PasswordResetResponse(
            message="Password has been reset successfully",
            success=True
        )

    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error in reset password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="An error occurred while processing your request",
                code="internal_error",
                success=False
            )
        )