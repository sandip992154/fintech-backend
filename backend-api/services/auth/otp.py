from fastapi import APIRouter, Depends, HTTPException, status
from services.integrations.email_service import EmailService
from services.schemas.schemas import OTPRequest
import logging

router = APIRouter(tags=["OTP"])
email_service = EmailService()
logger = logging.getLogger(__name__)

# In-memory OTP storage (replace with Redis in production)
otp_storage = {}

@router.post("/send-otp")
async def send_otp(request: OTPRequest):
    """Send OTP via email or SMS"""
    try:
        otp = generate_otp()  # From auth.py
        
        if request.otp_type == 'email':
            # Get user by email for personalization
            user = get_user_by_email(request.identifier)  # You'll need to implement this
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No user found with this email"
                )
            
            # Send OTP via email
            sent = email_service.send_otp_email(
                to_email=request.identifier,
                otp=otp,
                user_name=user.full_name
            )
            
            if not sent:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send OTP email"
                )
                
        elif request.otp_type == 'sms':
            # TODO: Implement SMS OTP sending when credentials are provided
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="SMS OTP not yet implemented"
            )
            
        # Store OTP with expiration (5 minutes)
        from datetime import datetime, timedelta
        otp_storage[request.identifier] = {
            'otp': otp,
            'expires_at': datetime.utcnow() + timedelta(minutes=5)
        }
        
        return {"message": f"OTP sent successfully via {request.otp_type}"}
        
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )

@router.post("/verify-otp")
async def verify_otp(request: OTPRequest, otp: str):
    """Verify OTP"""
    stored = otp_storage.get(request.identifier)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP request found"
        )
        
    if datetime.utcnow() > stored['expires_at']:
        del otp_storage[request.identifier]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )
        
    if otp != stored['otp']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
        
    # Clear used OTP
    del otp_storage[request.identifier]
    
    return {"message": "OTP verified successfully"}