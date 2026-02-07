"""
Pydantic schemas for User Management, KYC, and MPIN functionality
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator, constr
from typing import Optional, List
import re
from config.constants import VALIDATION_PATTERNS, KYC_STATUS, MPIN_CONFIG

# Base Models
class UserProfileBase(BaseModel):
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_address: Optional[str] = None
    business_phone: Optional[str] = None
    business_email: Optional[EmailStr] = None
    alternate_phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    language_preference: Optional[str] = "en"
    theme_preference: Optional[str] = "light"

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileOut(UserProfileBase):
    id: int
    user_code: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# KYC Schemas
class KYCDocumentBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    date_of_birth: str = Field(..., pattern=r"^\d{2}-\d{2}-\d{4}$")
    gender: Optional[str] = None
    pan_card_no: str = Field(..., pattern=VALIDATION_PATTERNS["PAN_CARD"])
    aadhar_card_no: str = Field(..., pattern=VALIDATION_PATTERNS["AADHAR_CARD"])
    address_line1: str = Field(..., min_length=10, max_length=200)
    address_line2: Optional[str] = None
    city: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=50)
    pincode: str = Field(..., pattern=VALIDATION_PATTERNS["PINCODE"])
    occupation: Optional[str] = None
    annual_income: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None

    @validator('pan_card_no')
    def validate_pan(cls, v):
        return v.upper()

    @validator('aadhar_card_no')
    def validate_aadhar(cls, v):
        if len(v) != 12:
            raise ValueError('Aadhar card must be 12 digits')
        return v

class KYCDocumentCreate(KYCDocumentBase):
    # Document URLs will be added after file upload
    pan_card_front: Optional[str] = None
    pan_card_back: Optional[str] = None
    aadhar_front: Optional[str] = None
    aadhar_back: Optional[str] = None
    photo: Optional[str] = None
    signature: Optional[str] = None
    address_proof: Optional[str] = None
    bank_statement: Optional[str] = None

class KYCDocumentUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None

class KYCDocumentOut(KYCDocumentBase):
    id: int
    user_code: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None
    
    # Document URLs
    pan_card_front: Optional[str] = None
    pan_card_back: Optional[str] = None
    aadhar_front: Optional[str] = None
    aadhar_back: Optional[str] = None
    photo: Optional[str] = None
    signature: Optional[str] = None
    address_proof: Optional[str] = None
    bank_statement: Optional[str] = None
    
    class Config:
        from_attributes = True

class KYCStatusResponse(BaseModel):
    user_code: str
    status: str
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

# MPIN Schemas
class MPINSetupRequest(BaseModel):
    mpin: constr(min_length=MPIN_CONFIG["MIN_LENGTH"], max_length=MPIN_CONFIG["MAX_LENGTH"])
    confirm_mpin: constr(min_length=MPIN_CONFIG["MIN_LENGTH"], max_length=MPIN_CONFIG["MAX_LENGTH"])
    
    @validator('mpin')
    def validate_mpin_format(cls, v):
        if not v.isdigit():
            raise ValueError('MPIN must contain only digits')
        return v
    
    @validator('confirm_mpin')
    def validate_confirm_mpin(cls, v, values):
        if 'mpin' in values and v != values['mpin']:
            raise ValueError('MPIN and Confirm MPIN do not match')
        return v

class MPINVerifyRequest(BaseModel):
    mpin: constr(min_length=MPIN_CONFIG["MIN_LENGTH"], max_length=MPIN_CONFIG["MAX_LENGTH"])
    
    @validator('mpin')
    def validate_mpin_format(cls, v):
        if not v.isdigit():
            raise ValueError('MPIN must contain only digits')
        return v

class MPINChangeRequest(BaseModel):
    old_mpin: constr(min_length=MPIN_CONFIG["MIN_LENGTH"], max_length=MPIN_CONFIG["MAX_LENGTH"])
    new_mpin: constr(min_length=MPIN_CONFIG["MIN_LENGTH"], max_length=MPIN_CONFIG["MAX_LENGTH"])
    confirm_new_mpin: constr(min_length=MPIN_CONFIG["MIN_LENGTH"], max_length=MPIN_CONFIG["MAX_LENGTH"])
    
    @validator('new_mpin')
    def validate_new_mpin(cls, v, values):
        if not v.isdigit():
            raise ValueError('MPIN must contain only digits')
        if 'old_mpin' in values and v == values['old_mpin']:
            raise ValueError('New MPIN cannot be same as old MPIN')
        return v
    
    @validator('confirm_new_mpin')
    def validate_confirm_new_mpin(cls, v, values):
        if 'new_mpin' in values and v != values['new_mpin']:
            raise ValueError('New MPIN and Confirm New MPIN do not match')
        return v

class MPINResetRequest(BaseModel):
    otp: str = Field(..., min_length=4, max_length=6)
    new_mpin: constr(min_length=MPIN_CONFIG["MIN_LENGTH"], max_length=MPIN_CONFIG["MAX_LENGTH"])
    confirm_new_mpin: constr(min_length=MPIN_CONFIG["MIN_LENGTH"], max_length=MPIN_CONFIG["MAX_LENGTH"])
    
    @validator('new_mpin')
    def validate_new_mpin(cls, v):
        if not v.isdigit():
            raise ValueError('MPIN must contain only digits')
        return v
    
    @validator('confirm_new_mpin')
    def validate_confirm_new_mpin(cls, v, values):
        if 'new_mpin' in values and v != values['new_mpin']:
            raise ValueError('New MPIN and Confirm New MPIN do not match')
        return v

class MPINStatusResponse(BaseModel):
    is_set: bool
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_locked: bool = False
    failed_attempts: int = 0

class MPINResponse(BaseModel):
    message: str
    success: bool = True
    is_locked: bool = False
    remaining_attempts: Optional[int] = None

# File Upload Schemas
class FileUploadResponse(BaseModel):
    url: str
    public_id: str
    filename: str
    size: int
    format: str

class DocumentUploadRequest(BaseModel):
    document_type: str = Field(..., pattern="^(pan_card_front|pan_card_back|aadhar_front|aadhar_back|photo|signature|address_proof|bank_statement)$")

# OTP Schemas
class OTPGenerateRequest(BaseModel):
    purpose: str = Field(..., pattern="^(mpin_setup|kyc_verification|mpin_reset|login)$")

class OTPVerifyRequest(BaseModel):
    otp: str = Field(..., min_length=4, max_length=6)
    purpose: str = Field(..., pattern="^(mpin_setup|kyc_verification|mpin_reset|login)$")

class OTPResponse(BaseModel):
    message: str
    success: bool = True
    expires_at: Optional[datetime] = None

# Enhanced User Schemas with new fields
class UserCreateEnhanced(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=VALIDATION_PATTERNS["PHONE"])
    password: str = Field(..., min_length=8)
    role: str
    
    # Optional profile fields
    business_name: Optional[str] = None
    business_type: Optional[str] = None

class UserOutEnhanced(BaseModel):
    id: int
    user_code: str
    full_name: str
    email: str
    phone: str
    role: str
    is_active: bool
    created_at: datetime
    
    # Status fields
    kyc_status: Optional[str] = None
    mpin_set: bool = False
    profile_complete: bool = False
    
    class Config:
        from_attributes = True

# Member Management Schemas
class MemberCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=VALIDATION_PATTERNS["PHONE"])
    role: str
    business_name: Optional[str] = None
    
class MemberListResponse(BaseModel):
    members: List[UserOutEnhanced]
    total: int
    page: int
    limit: int
    
# KYC Review Schemas (for Super Admin)
class KYCReviewRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None

class KYCReviewResponse(BaseModel):
    message: str
    success: bool = True
    kyc_id: int
    decision: str
