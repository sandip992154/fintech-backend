from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from database.database import get_db
from services.auth.mpin_service import (
    get_user_by_identifier,
    verify_user_otp,
    create_mpin,
    verify_mpin,
    update_mpin,
    reset_mpin,
    get_mpin_status
)
from services.schemas.mpin_schemas import (
    MPINSetup,
    MPINLogin,
    MPINUpdate,
    MPINReset,
    MPINStatus,
    MPINResponse
)

router = APIRouter(
    prefix="/api/v1/mpin",
    tags=["MPIN Management"]
)

@router.post("/setup", response_model=MPINResponse)
async def setup_mpin(
    setup_data: MPINSetup,
    db: Session = Depends(get_db)
) -> Any:
    """
    Setup MPIN for a user.
    
    - Accepts email, phone, or user_code as identifier
    - Requires OTP verification
    - MPIN must be exactly 4 digits
    """
    user = get_user_by_identifier(db, setup_data.identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if not verify_user_otp(db, user, setup_data.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
        
    create_mpin(db, user, setup_data.mpin)
    return {"message": "MPIN setup successful", "status": True}

@router.post("/login", response_model=MPINResponse)
async def login_with_mpin(
    login_data: MPINLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    Login using MPIN.
    
    - Accepts email, phone, or user_code as identifier
    - Returns auth token on successful verification
    """
    user = get_user_by_identifier(db, login_data.identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if not verify_mpin(db, user, login_data.mpin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MPIN"
        )
        
    # Generate and return auth token (implement your token generation logic)
    return {"message": "Login successful", "status": True}

@router.post("/update", response_model=MPINResponse)
async def update_user_mpin(
    update_data: MPINUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Update existing MPIN.
    
    - Requires old MPIN verification
    - Requires OTP verification
    - New MPIN must be exactly 4 digits
    """
    user = get_user_by_identifier(db, update_data.identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if not verify_user_otp(db, user, update_data.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
        
    update_mpin(db, user, update_data.old_mpin, update_data.mpin)
    return {"message": "MPIN updated successfully", "status": True}

@router.post("/reset", response_model=MPINResponse)
async def reset_user_mpin(
    reset_data: MPINReset,
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset MPIN using OTP verification.
    
    - Requires OTP verification
    - New MPIN must be exactly 4 digits
    """
    user = get_user_by_identifier(db, reset_data.identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if not verify_user_otp(db, user, reset_data.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
        
    reset_mpin(db, user, reset_data.new_mpin)
    return {"message": "MPIN reset successful", "status": True}

@router.get("/status/{identifier}", response_model=MPINStatus)
async def check_mpin_status(
    identifier: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Check if MPIN is set for a user.
    
    - Returns MPIN status and related timestamps
    """
    user = get_user_by_identifier(db, identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return get_mpin_status(db, user)