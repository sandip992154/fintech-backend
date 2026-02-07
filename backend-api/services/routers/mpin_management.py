"""
MPIN Management APIs for setup, verification, change, and reset functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
import secrets
import string

from database.database import get_db
from services.auth.auth import get_current_user
from services.models.models import User
from services.models.user_models import MPIN, OTP
from services.schemas.user_schemas import (
    MPINSetupRequest, MPINVerifyRequest, MPINChangeRequest, MPINResetRequest,
    MPINStatusResponse, MPINResponse, OTPGenerateRequest, OTPVerifyRequest, OTPResponse
)
from config.constants import MPIN_CONFIG, OTP_LENGTH, OTP_EXPIRY_MINUTES
from utils.notification_utils import send_otp_email

router = APIRouter(prefix="/mpin", tags=["MPIN Management"])

# Password context for MPIN hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_mpin(mpin: str) -> str:
    """Hash MPIN using bcrypt"""
    return pwd_context.hash(mpin)

def verify_mpin(plain_mpin: str, hashed_mpin: str) -> bool:
    """Verify MPIN against hash"""
    return pwd_context.verify(plain_mpin, hashed_mpin)

def generate_otp() -> str:
    """Generate random OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))

def is_mpin_locked(mpin_record: MPIN) -> bool:
    """Check if MPIN is currently locked"""
    if mpin_record.locked_until and mpin_record.locked_until > datetime.utcnow():
        return True
    return False

def lock_mpin(mpin_record: MPIN, db: Session):
    """Lock MPIN for specified duration"""
    mpin_record.locked_until = datetime.utcnow() + timedelta(
        minutes=MPIN_CONFIG["LOCK_DURATION_MINUTES"]
    )
    mpin_record.failed_attempts = 0  # Reset attempts after locking
    db.commit()

@router.get("/status", response_model=MPINStatusResponse)
async def get_mpin_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's MPIN status"""
    mpin = db.query(MPIN).filter(
        MPIN.user_code == current_user.user_code
    ).first()
    
    if not mpin:
        return MPINStatusResponse(
            is_set=False,
            is_locked=False,
            failed_attempts=0
        )
    
    return MPINStatusResponse(
        is_set=mpin.is_set,
        created_at=mpin.created_at,
        last_used=mpin.last_used,
        is_locked=is_mpin_locked(mpin),
        failed_attempts=mpin.failed_attempts
    )

@router.post("/setup", response_model=MPINResponse)
async def setup_mpin(
    mpin_data: MPINSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup MPIN for first time"""
    # Check if MPIN already exists
    existing_mpin = db.query(MPIN).filter(
        MPIN.user_code == current_user.user_code
    ).first()
    
    if existing_mpin and existing_mpin.is_set:
        raise HTTPException(
            status_code=400,
            detail="MPIN is already set. Use change MPIN endpoint to update."
        )
    
    # Hash the MPIN
    hashed_mpin = hash_mpin(mpin_data.mpin)
    
    if existing_mpin:
        # Update existing record
        existing_mpin.mpin_hash = hashed_mpin
        existing_mpin.is_set = True
        existing_mpin.failed_attempts = 0
        existing_mpin.locked_until = None
        existing_mpin.updated_at = datetime.utcnow()
        
        db.commit()
        mpin_record = existing_mpin
    else:
        # Create new MPIN record
        mpin_record = MPIN(
            user_id=current_user.id,
            user_code=current_user.user_code,
            mpin_hash=hashed_mpin,
            is_set=True
        )
        
        db.add(mpin_record)
        db.commit()
    
    return MPINResponse(
        message="MPIN setup successfully",
        success=True
    )

@router.post("/verify", response_model=MPINResponse)
async def verify_mpin_endpoint(
    verify_data: MPINVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify MPIN"""
    mpin = db.query(MPIN).filter(
        MPIN.user_code == current_user.user_code
    ).first()
    
    if not mpin or not mpin.is_set:
        raise HTTPException(
            status_code=400,
            detail="MPIN is not set"
        )
    
    # Check if MPIN is locked
    if is_mpin_locked(mpin):
        remaining_time = (mpin.locked_until - datetime.utcnow()).total_seconds() / 60
        raise HTTPException(
            status_code=423,
            detail=f"MPIN is locked. Try again in {int(remaining_time)} minutes."
        )
    
    # Verify MPIN
    if verify_mpin(verify_data.mpin, mpin.mpin_hash):
        # Success - reset failed attempts and update last used
        mpin.failed_attempts = 0
        mpin.last_used = datetime.utcnow()
        mpin.last_attempt_at = datetime.utcnow()
        db.commit()
        
        return MPINResponse(
            message="MPIN verified successfully",
            success=True
        )
    else:
        # Failed attempt
        mpin.failed_attempts += 1
        mpin.last_attempt_at = datetime.utcnow()
        
        remaining_attempts = MPIN_CONFIG["MAX_ATTEMPTS"] - mpin.failed_attempts
        
        # Lock if max attempts reached
        if mpin.failed_attempts >= MPIN_CONFIG["MAX_ATTEMPTS"]:
            lock_mpin(mpin, db)
            raise HTTPException(
                status_code=423,
                detail=f"MPIN locked due to {MPIN_CONFIG['MAX_ATTEMPTS']} failed attempts. Try again in {MPIN_CONFIG['LOCK_DURATION_MINUTES']} minutes."
            )
        
        db.commit()
        
        return MPINResponse(
            message="Invalid MPIN",
            success=False,
            remaining_attempts=remaining_attempts
        )

@router.put("/change", response_model=MPINResponse)
async def change_mpin(
    change_data: MPINChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change existing MPIN"""
    mpin = db.query(MPIN).filter(
        MPIN.user_code == current_user.user_code
    ).first()
    
    if not mpin or not mpin.is_set:
        raise HTTPException(
            status_code=400,
            detail="MPIN is not set. Use setup endpoint first."
        )
    
    # Check if MPIN is locked
    if is_mpin_locked(mpin):
        remaining_time = (mpin.locked_until - datetime.utcnow()).total_seconds() / 60
        raise HTTPException(
            status_code=423,
            detail=f"MPIN is locked. Try again in {int(remaining_time)} minutes."
        )
    
    # Verify old MPIN
    if not verify_mpin(change_data.old_mpin, mpin.mpin_hash):
        mpin.failed_attempts += 1
        remaining_attempts = MPIN_CONFIG["MAX_ATTEMPTS"] - mpin.failed_attempts
        
        if mpin.failed_attempts >= MPIN_CONFIG["MAX_ATTEMPTS"]:
            lock_mpin(mpin, db)
            raise HTTPException(
                status_code=423,
                detail="MPIN locked due to failed attempts"
            )
        
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Invalid old MPIN. {remaining_attempts} attempts remaining."
        )
    
    # Update with new MPIN
    mpin.mpin_hash = hash_mpin(change_data.new_mpin)
    mpin.failed_attempts = 0
    mpin.locked_until = None
    mpin.updated_at = datetime.utcnow()
    
    db.commit()
    
    return MPINResponse(
        message="MPIN changed successfully",
        success=True
    )

# OTP Management for MPIN Reset
@router.post("/generate-otp", response_model=OTPResponse)
async def generate_mpin_reset_otp(
    otp_request: OTPGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate OTP for MPIN reset"""
    if otp_request.purpose != "mpin_reset":
        raise HTTPException(status_code=400, detail="Invalid OTP purpose")
    
    # Check if user has MPIN set
    mpin = db.query(MPIN).filter(
        MPIN.user_code == current_user.user_code
    ).first()
    
    if not mpin or not mpin.is_set:
        raise HTTPException(status_code=400, detail="MPIN is not set")
    
    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Save OTP to database
    otp_record = OTP(
        user_code=current_user.user_code,
        phone=current_user.phone,
        email=current_user.email,
        otp_code=otp_code,
        purpose=otp_request.purpose,
        expires_at=expires_at
    )
    
    db.add(otp_record)
    db.commit()
    
    # Send OTP via SMS and Email
    try:
        send_otp_email(current_user.email, otp_code, current_user.full_name)
        send_otp_email(current_user.email, otp_code, current_user.full_name)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send OTP: {str(e)}")
    
    return OTPResponse(
        message="OTP sent successfully",
        success=True,
        expires_at=expires_at
    )

@router.post("/verify-otp", response_model=OTPResponse)
async def verify_otp(
    otp_request: OTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify OTP for MPIN reset"""
    # Find valid OTP
    otp_record = db.query(OTP).filter(
        OTP.user_code == current_user.user_code,
        OTP.otp_code == otp_request.otp,
        OTP.purpose == otp_request.purpose,
        OTP.is_used == False,
        OTP.is_expired == False,
        OTP.expires_at > datetime.utcnow()
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP"
        )
    
    # Mark OTP as used
    otp_record.is_used = True
    otp_record.used_at = datetime.utcnow()
    db.commit()
    
    return OTPResponse(
        message="OTP verified successfully",
        success=True
    )

@router.post("/reset", response_model=MPINResponse)
async def reset_mpin(
    reset_data: MPINResetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset MPIN using OTP"""
    # Verify OTP first
    otp_record = db.query(OTP).filter(
        OTP.user_code == current_user.user_code,
        OTP.otp_code == reset_data.otp,
        OTP.purpose == "mpin_reset",
        OTP.is_used == True,  # Must be verified first
        OTP.used_at > datetime.utcnow() - timedelta(minutes=5)  # Used within last 5 minutes
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP or OTP not verified"
        )
    
    # Get MPIN record
    mpin = db.query(MPIN).filter(
        MPIN.user_code == current_user.user_code
    ).first()
    
    if not mpin:
        raise HTTPException(status_code=400, detail="MPIN record not found")
    
    # Reset MPIN
    mpin.mpin_hash = hash_mpin(reset_data.new_mpin)
    mpin.failed_attempts = 0
    mpin.locked_until = None
    mpin.updated_at = datetime.utcnow()
    
    # Mark OTP as expired to prevent reuse
    otp_record.is_expired = True
    
    db.commit()
    
    return MPINResponse(
        message="MPIN reset successfully",
        success=True
    )

@router.delete("/remove")
async def remove_mpin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove MPIN (Admin only for testing)"""
    if current_user.role.name not in ["super_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    mpin = db.query(MPIN).filter(
        MPIN.user_code == current_user.user_code
    ).first()
    
    if mpin:
        db.delete(mpin)
        db.commit()
    
    return {
        "message": "MPIN removed successfully",
        "success": True
    }