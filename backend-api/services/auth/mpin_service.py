from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from services.models.user_models import MPIN
from services.models.models import User
from utils.security import get_password_hash, verify_password
from utils.email_utils import send_otp_email

def get_user_by_identifier(db: Session, identifier: str) -> User:
    """Get user by email, phone, or user_code"""
    return (
        db.query(User)
        .filter(
            (User.email == identifier) |
            (User.phone == identifier) |
            (User.user_code == identifier)
        )
        .first()
    )

def verify_user_otp(db: Session, user: User, otp: str) -> bool:
    """Verify OTP for the user"""
    # Implement OTP verification logic here
    # This should match your existing OTP verification system
    return True  # Placeholder - implement actual verification

def create_mpin(db: Session, user: User, mpin: str) -> MPIN:
    """Create or update MPIN for a user"""
    existing_mpin = db.query(MPIN).filter(MPIN.user_code == user.user_code).first()
    
    if existing_mpin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MPIN already exists for this user"
        )

    mpin_hash = get_password_hash(mpin)
    db_mpin = MPIN(
        user_id=user.id,
        user_code=user.user_code,
        mpin_hash=mpin_hash,
        is_set=True
    )
    
    db.add(db_mpin)
    db.commit()
    db.refresh(db_mpin)
    return db_mpin

def verify_mpin(db: Session, user: User, mpin: str) -> bool:
    """Verify MPIN for a user"""
    db_mpin = db.query(MPIN).filter(MPIN.user_code == user.user_code).first()
    
    if not db_mpin or not db_mpin.is_set:
        return False
        
    is_valid = verify_password(mpin, db_mpin.mpin_hash)
    
    if is_valid:
        db_mpin.last_used = datetime.utcnow()
        db.commit()
        
    return is_valid

def update_mpin(db: Session, user: User, old_mpin: str, new_mpin: str) -> MPIN:
    """Update MPIN for a user"""
    db_mpin = db.query(MPIN).filter(MPIN.user_code == user.user_code).first()
    
    if not db_mpin or not db_mpin.is_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MPIN not found or inactive"
        )
        
    if not verify_password(old_mpin, db_mpin.mpin_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old MPIN"
        )
        
    db_mpin.mpin_hash = get_password_hash(new_mpin)
    db_mpin.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_mpin)
    return db_mpin

def reset_mpin(db: Session, user: User, new_mpin: str) -> MPIN:
    """Reset MPIN for a user (after OTP verification)"""
    db_mpin = db.query(MPIN).filter(MPIN.user_code == user.user_code).first()
    
    if not db_mpin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MPIN not found"
        )
        
    db_mpin.mpin_hash = get_password_hash(new_mpin)
    db_mpin.updated_at = datetime.utcnow()
    db_mpin.is_set = True
    db.commit()
    db.refresh(db_mpin)
    return db_mpin

def get_mpin_status(db: Session, user: User) -> dict:
    """Get MPIN status for a user"""
    db_mpin = db.query(MPIN).filter(MPIN.user_code == user.user_code).first()
    
    if not db_mpin:
        return {
            "is_set": False,
            "created_at": None,
            "last_used": None
        }
        
    return {
        "is_set": db_mpin.is_set,
        "created_at": db_mpin.created_at,
        "last_used": db_mpin.last_used
    }