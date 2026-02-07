from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class KYCStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    HOLD = "hold"
    NOT_SUBMITTED = "not_submitted"

class BusinessType(str, Enum):
    RETAIL = "Retail"
    WHOLESALE = "Wholesale"
    SERVICE = "Service"
    MANUFACTURING = "Manufacturing"

class AddressProofType(str, Enum):
    AADHAR = "Aadhar"
    UTILITY_BILL = "Utility Bill"
    RENTAL_AGREEMENT = "Rental Agreement"

class KYCCreate(BaseModel):
    # Business Information
    shop_name: str = Field(..., min_length=3)
    business_type: BusinessType
    business_category: str
    
    # Tax & Registration Numbers
    gst_no: Optional[str] = Field(None, min_length=15, max_length=15, pattern="^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
    pan_card_no: str = Field(..., min_length=10, max_length=10, pattern="^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    company_pan_no: Optional[str] = Field(None, min_length=10, max_length=10, pattern="^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    aadhar_card_no: str = Field(..., min_length=12, max_length=12, pattern="^[0-9]{12}$")
    business_registration_no: Optional[str]
    trade_license_no: Optional[str]
    
    # Document URLs
    profile_photo_url: str
    address_proof_type: Optional[AddressProofType]
    address_proof_url: Optional[str]
    company_pan_url: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "shop_name": "My Shop Name",
                "business_type": "Retail",
                "business_category": "Electronics",
                "gst_no": "29ABCDE1234F1Z5",
                "pan_card_no": "ABCDE1234F",
                "company_pan_no": "ABCDE1234F",
                "aadhar_card_no": "123456789012",
                "profile_photo_url": "https://example.com/photo.jpg"
            }
        }

class KYCResponse(BaseModel):
    id: int
    user_code: str
    shop_name: str
    business_type: str
    business_category: str
    gst_no: Optional[str]
    pan_card_no: str
    company_pan_no: Optional[str]
    aadhar_card_no: str
    business_registration_no: Optional[str]
    trade_license_no: Optional[str]
    profile_photo_url: str
    address_proof_type: Optional[str]
    address_proof_url: Optional[str]
    company_pan_url: Optional[str]
    status: KYCStatus
    submitted_at: datetime
    verified_at: Optional[datetime]
    rejection_reason: Optional[str]

    class Config:
        from_attributes = True

class KYCStatusCheck(BaseModel):
    status: KYCStatus
    message: str
    kyc_data: Optional[KYCResponse] = None

class KYCVerifyRequest(BaseModel):
    action: str = Field(..., pattern="^(accept|reject|hold)$")
    rejection_reason: Optional[str] = None