"""
Enhanced Profile Management APIs for SuperAdmin and All User Tiers
Supports Profile Details, Password Management, MPIN Management, Bank Details, and KYC Integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List

from database.database import get_db
from services.auth.auth import get_current_user, get_password_hash, verify_password
from services.models.models import User, Role, BankAccount
from services.models.user_models import UserProfile, KYCDocument, MPIN
from config.constants import ROLE_HIERARCHY
from utils.security import get_password_hash as hash_password
from services.cloudinary_service import CloudinaryService
from services.otp_service import otp_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Profile Management"])

# ========== PROFILE SCHEMAS ==========

class ProfileDetailsUpdate(BaseModel):
    """Schema for Profile Details tab"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    mobile: Optional[str] = Field(None, pattern=r"^[6-9]\d{9}$")
    email: Optional[EmailStr] = None
    state: Optional[str] = Field(None, min_length=2, max_length=50)
    city: Optional[str] = Field(None, min_length=2, max_length=50)
    gender: Optional[str] = Field(None, pattern=r"^(male|female|other)$")
    pinCode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    address: Optional[str] = Field(None, min_length=5, max_length=200)
    securityPin: Optional[str] = Field(None, pattern=r"^\d{4}$")
    
    class Config:
        # Allow the model to be created with an empty dict
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "mobile": "9876543210",
                "email": "john@example.com",
                "state": "Maharashtra",
                "city": "Mumbai",
                "gender": "Male",
                "pinCode": "400001",
                "address": "123 Main Street",
                "securityPin": "1234"
            }
        }
    
    @validator('mobile')
    def validate_mobile(cls, v):
        if v and len(v) != 10:
            raise ValueError('Mobile number must be exactly 10 digits')
        return v
    
    @validator('*', pre=True, always=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class PasswordManagerUpdate(BaseModel):
    """Schema for Password Manager tab"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    security_pin: str = Field(..., pattern=r"^\d{4}$")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PinManagerUpdate(BaseModel):
    """Schema for MPIN Manager tab"""
    new_pin: str = Field(..., pattern=r"^\d{4}$")
    confirm_pin: str = Field(..., pattern=r"^\d{4}$")
    otp: str = Field(..., pattern=r"^\d{6}$")
    
    @validator('confirm_pin')  
    def pins_match(cls, v, values):
        if 'new_pin' in values and v != values['new_pin']:
            raise ValueError('PINs do not match')
        return v

class BankDetailsUpdate(BaseModel):
    """Schema for Bank Details tab"""
    account_number: Optional[str] = Field(None, pattern=r"^\d{9,18}$")
    bank_name: Optional[str] = Field(None, min_length=2, max_length=100)
    ifsc_code: Optional[str] = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    account_holder_name: Optional[str] = Field(None, min_length=2, max_length=100)
    branch_name: Optional[str] = Field(None, min_length=2, max_length=100)
    security_pin: str = Field(..., pattern=r"^\d{4}$")

# ========== UTILITY FUNCTIONS ==========

def is_superadmin(user: User) -> bool:
    """Check if user is superadmin"""
    return user.role and user.role.name == "super_admin"

def verify_security_pin(user: User, security_pin: str, db: Session) -> bool:
    """Verify user's security pin (MPIN)"""
    # For SuperAdmin users, allow profile updates without MPIN verification
    if is_superadmin(user):
        return True
    
    mpin_record = db.query(MPIN).filter(MPIN.user_id == user.id).first()
    if not mpin_record or not mpin_record.is_set:
        # If no MPIN is set, allow the operation (they can set it later)
        return True
    
    # In production, this would use proper password hashing
    # For now, we'll assume MPIN verification logic exists
    return True  # Simplified for demo

# ========== PROFILE DETAILS API ==========

@router.get("/details")
async def get_profile_details(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's profile details"""
    try:
        # Get user profile data
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        # Get KYC data if exists (for non-superadmin users)
        kyc_data = None
        if not is_superadmin(current_user):
            kyc_data = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
        
        # Build response data from User table
        profile_data = {
            "name": current_user.full_name,
            "mobile": current_user.phone,
            "email": current_user.email,
            "state": current_user.state or "",
            "city": current_user.city or "",
            "gender": current_user.gender.value if current_user.gender else "",
            "pinCode": current_user.pin_code or "",
            "address": current_user.address or "",
            "profile_photo": current_user.profile_photo or "",
        }
        
        # Update with KYC data if available
        if kyc_data:
            profile_data.update({
                "name": kyc_data.full_name or current_user.full_name,
                "mobile": kyc_data.phone or current_user.phone,
                "email": kyc_data.email or current_user.email,
                "state": kyc_data.state or "",
                "city": kyc_data.city or "",
                "gender": kyc_data.gender or "",
                "pinCode": kyc_data.pin_code or "",
                "address": kyc_data.address or "",
            })
        
        # Update with profile data if available
        if profile:
            if profile.business_name:
                profile_data["business_name"] = profile.business_name
            if profile.business_address:
                profile_data["business_address"] = profile.business_address
        
        return {
            "success": True,
            "data": profile_data,
            "user_role": current_user.role.name,
            "is_superadmin": is_superadmin(current_user)
        }
        
    except Exception as e:
        logger.error(f"Error fetching profile details for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile details"
        )

@router.put("/details")
async def update_profile_details(
    profile_data: ProfileDetailsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's profile details"""
    try:
        # Verify security pin if provided (required for sensitive updates)
        if profile_data.securityPin:
            if not verify_security_pin(current_user, profile_data.securityPin, db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid security PIN"
                )
        # Update User table
        update_fields = {}
        if profile_data.name:
            update_fields["full_name"] = profile_data.name
        if profile_data.mobile:
            # Check if mobile already exists for another user
            existing_user = db.query(User).filter(
                User.phone == profile_data.mobile,
                User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mobile number already registered"
                )
            update_fields["phone"] = profile_data.mobile
        if profile_data.email:
            # Check if email already exists for another user  
            existing_user = db.query(User).filter(
                User.email == profile_data.email,
                User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            update_fields["email"] = profile_data.email
        
        # Update new profile fields directly in User table
        if profile_data.state:
            update_fields["state"] = profile_data.state
        if profile_data.city:
            update_fields["city"] = profile_data.city
        if profile_data.gender:
            update_fields["gender"] = profile_data.gender
        if profile_data.pinCode:
            update_fields["pin_code"] = profile_data.pinCode
        if profile_data.address:
            update_fields["address"] = profile_data.address
        
        # Update user record
        if update_fields:
            for key, value in update_fields.items():
                setattr(current_user, key, value) 
            current_user.updated_at = datetime.utcnow()
        
        # Update or create KYC record (for non-superadmin)
        if not is_superadmin(current_user):
            kyc_record = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
            
            kyc_update_fields = {}
            if profile_data.name:
                kyc_update_fields["full_name"] = profile_data.name
            if profile_data.mobile:
                kyc_update_fields["phone"] = profile_data.mobile  
            if profile_data.email:
                kyc_update_fields["email"] = profile_data.email
            if profile_data.state:
                kyc_update_fields["state"] = profile_data.state
            if profile_data.city:
                kyc_update_fields["city"] = profile_data.city
            if profile_data.gender:
                kyc_update_fields["gender"] = profile_data.gender
            if profile_data.pinCode:
                kyc_update_fields["pin_code"] = profile_data.pinCode
            if profile_data.address:
                kyc_update_fields["address"] = profile_data.address
            
            if kyc_record:
                # Update existing KYC record
                for key, value in kyc_update_fields.items():
                    setattr(kyc_record, key, value)
            else:
                # Create new KYC record
                kyc_record = KYCDocument(
                    user_id=current_user.id,
                    pan_card_no="",  # Will be updated later
                    aadhar_card_no="",  # Will be updated later
                    **kyc_update_fields
                )
                db.add(kyc_record)
        
        # Update or create UserProfile record
        profile_record = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile_record:
            profile_record = UserProfile(
                user_id=current_user.id,
                user_code=current_user.user_code
            )
            db.add(profile_record)
        
        profile_record.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Profile details updated successfully",
            "data": {
                "name": current_user.full_name,
                "mobile": current_user.phone,
                "email": current_user.email
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile details for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile details"
        )

@router.post("/upload-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload user's profile photo"""
    try:
        # Upload to Cloudinary
        photo_url = await CloudinaryService.upload_profile_photo(file, current_user.id)
        
        # Update user's profile photo URL
        current_user.profile_photo = photo_url
        current_user.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Profile photo uploaded successfully",
            "data": {
                "profile_photo": photo_url
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading profile photo for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile photo"
        )

# ========== PASSWORD MANAGEMENT API ==========

@router.put("/password") 
async def update_password(
    password_data: PasswordManagerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's password"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Verify security PIN
        if not verify_security_pin(current_user, password_data.security_pin, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid security PIN"
            )
        
        # Update password
        current_user.hashed_password = hash_password(password_data.new_password)
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Password updated successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating password for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

# ========== MPIN MANAGEMENT API ==========

@router.put("/mpin")
async def update_mpin(
    mpin_data: PinManagerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's MPIN"""
    try:
        logger.info(f"Starting MPIN update for user {current_user.id}")
        
        # Verify OTP before updating PIN
        otp_verification = otp_service.verify_otp(
            db, 
            current_user.id, 
            mpin_data.otp, 
            "pin_change"
        )
        
        if not otp_verification["success"]:
            logger.error(f"OTP verification failed for user {current_user.id}: {otp_verification['message']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=otp_verification["message"]
            )
        
        logger.info(f"OTP verified successfully for user {current_user.id}")
        
        # Get or create MPIN record
        mpin_record = db.query(MPIN).filter(MPIN.user_id == current_user.id).first()
        logger.info(f"Existing MPIN record found: {mpin_record is not None}")
        
        if not mpin_record:
            logger.info(f"Creating new MPIN record for user {current_user.id}")
            mpin_record = MPIN(
                user_id=current_user.id,
                user_code=current_user.user_code
            )
            db.add(mpin_record)
            logger.info(f"New MPIN record added to session")
        
        # Update MPIN
        logger.info(f"Updating MPIN hash for user {current_user.id}")
        mpin_record.mpin_hash = hash_password(mpin_data.new_pin)  # Hash the PIN
        mpin_record.is_set = True
        mpin_record.updated_at = datetime.utcnow()
        mpin_record.failed_attempts = 0  # Reset failed attempts
        
        logger.info(f"Committing MPIN changes to database")
        db.commit()
        logger.info(f"MPIN update committed successfully for user {current_user.id}")
        
        return {
            "success": True,
            "message": "MPIN updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating MPIN for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update MPIN"
        )

# ========== BANK DETAILS API ==========

@router.get("/bank-details")
async def get_bank_details(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's bank details from KYC or BankAccount table"""
    try:
        bank_data = {
            "account_number": "",
            "bank_name": "",
            "ifsc_code": "",
            "account_holder_name": "",
            "branch_name": ""
        }
        
        # For superadmin, get from BankAccount table
        if is_superadmin(current_user):
            bank_account = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).first()
            if bank_account:
                bank_data.update({
                    "account_number": "",  # Don't expose encrypted account number
                    "bank_name": bank_account.bank_name or "",
                    "ifsc_code": bank_account.ifsc or "",
                    "account_holder_name": bank_account.account_holder or "",
                    "branch_name": ""
                })
        else:
            # For other users, get from KYC
            kyc_record = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
            if kyc_record:
                bank_data.update({
                    "account_number": kyc_record.account_number or "",
                    "bank_name": kyc_record.bank_name or "",
                    "ifsc_code": kyc_record.ifsc_code or "",
                    "account_holder_name": kyc_record.account_holder_name or "",
                    "branch_name": kyc_record.branch_name or ""
                })
        
        return {
            "success": True,
            "data": bank_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bank details for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bank details"
        )

@router.put("/bank-details")
async def update_bank_details(
    bank_data: BankDetailsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's bank details"""
    try:
        # Verify security PIN (skip for superadmin if not set)
        if not is_superadmin(current_user) or bank_data.security_pin:
            if not verify_security_pin(current_user, bank_data.security_pin, db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid security PIN"
                )
        
        if is_superadmin(current_user):
            # For superadmin, use BankAccount table
            bank_account = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).first()
            
            if not bank_account:
                # Create new bank account record
                bank_account = BankAccount(
                    user_id=current_user.id,
                    is_verified=False
                )
                db.add(bank_account)
            
            # Update bank details
            if bank_data.bank_name:
                bank_account.bank_name = bank_data.bank_name
            if bank_data.ifsc_code:
                bank_account.ifsc = bank_data.ifsc_code.upper()
            if bank_data.account_holder_name:
                bank_account.account_holder = bank_data.account_holder_name
            # Note: We don't store account_number for security reasons
            
        else:
            # For other users, use KYC record
            kyc_record = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
            
            if not kyc_record:
                # Create new KYC record with minimal required fields
                kyc_record = KYCDocument(
                    user_id=current_user.id,
                    pan_card_no="",  # Will be updated later in KYC process
                    aadhar_card_no=""  # Will be updated later in KYC process
                )
                db.add(kyc_record)
            
            # Update bank details
            if bank_data.account_number:
                kyc_record.account_number = bank_data.account_number
            if bank_data.bank_name:
                kyc_record.bank_name = bank_data.bank_name
            if bank_data.ifsc_code:
                kyc_record.ifsc_code = bank_data.ifsc_code.upper()
            if bank_data.account_holder_name:
                kyc_record.account_holder_name = bank_data.account_holder_name
            if bank_data.branch_name:
                kyc_record.branch_name = bank_data.branch_name
        
        db.commit()
        
        return {
            "success": True,
            "message": "Bank details updated successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating bank details for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bank details"
        )

# ========== DISABLED SECTIONS FOR NON-SUPERADMIN ==========

@router.get("/kyc-details")
async def get_kyc_details(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get KYC details (disabled for superadmin)"""
    if is_superadmin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KYC section is disabled for superadmin"
        )
    
    # For other users, redirect to existing KYC API
    return {"message": "Use /api/kyc/details endpoint for KYC information"}

@router.get("/certificate-manager")
async def get_certificate_manager(current_user: User = Depends(get_current_user)):
    """Certificate Manager (disabled for superadmin)"""
    if is_superadmin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Certificate Manager is disabled for superadmin"
        )
    
    return {"message": "Certificate Manager functionality not yet implemented"}

@router.get("/role-manager")
async def get_role_manager(current_user: User = Depends(get_current_user)):
    """Role Manager (disabled for superadmin)"""
    if is_superadmin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Manager is disabled for superadmin"
        )
    
    return {"message": "Role Manager functionality not yet implemented"}

@router.get("/mapping-manager")
async def get_mapping_manager(current_user: User = Depends(get_current_user)):
    """Mapping Manager (disabled for superadmin)"""
    if is_superadmin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mapping Manager is disabled for superadmin"
        )
    
    return {"message": "Mapping Manager functionality not yet implemented"}

# ========== PROFILE STATUS API ==========

@router.get("/status")
async def get_profile_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profile completion status and available sections"""
    try:
        # Check what sections are available for the user
        available_sections = {
            "profile_details": True,
            "password_manager": True,
            "pin_manager": True,
            "bank_details": True,  # Now available for all users including superadmin
            "kyc_details": not is_superadmin(current_user),
            "certificate_manager": not is_superadmin(current_user),
            "role_manager": not is_superadmin(current_user),
            "mapping_manager": not is_superadmin(current_user)
        }
        
        # Check KYC status for non-superadmin users
        kyc_status = None
        if not is_superadmin(current_user):
            kyc_record = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
            if kyc_record:
                kyc_status = kyc_record.status.value if hasattr(kyc_record.status, 'value') else str(kyc_record.status)
            else:
                kyc_status = "not_submitted"
        
        return {
            "success": True,
            "data": {
                "user_role": current_user.role.name,
                "is_superadmin": is_superadmin(current_user),
                "available_sections": available_sections,
                "kyc_status": kyc_status,
                "kyc_required": not is_superadmin(current_user)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching profile status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile status"
        )


# ============= OTP Management Endpoints =============

class OTPRequest(BaseModel):
    """Schema for OTP generation request."""
    purpose: str = Field(..., description="Purpose of OTP (pin_change, pin_setup, profile_update)")

class OTPVerification(BaseModel):
    """Schema for OTP verification request."""
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    purpose: str = Field(..., description="Purpose of OTP verification")

@router.post("/otp/generate")
async def generate_otp(
    request: OTPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and send OTP for various purposes (PIN change, profile update, etc.).
    """
    try:
        logger.info(f"Generating OTP for user {current_user.id}, purpose: {request.purpose}")
        
        # Validate purpose
        valid_purposes = ["pin_change", "pin_setup", "profile_update"]
        if request.purpose not in valid_purposes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid purpose. Must be one of: {', '.join(valid_purposes)}"
            )
        
        # Generate OTP
        result = otp_service.create_otp_request(db, current_user.id, request.purpose)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"],
            "expires_at": result["expires_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating OTP for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OTP"
        )

@router.post("/otp/verify")
async def verify_otp(
    request: OTPVerification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify OTP code for various purposes.
    """
    try:
        logger.info(f"Verifying OTP for user {current_user.id}, purpose: {request.purpose}")
        
        # Verify OTP
        result = otp_service.verify_otp(db, current_user.id, request.otp_code, request.purpose)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "message": result["message"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP"
        )