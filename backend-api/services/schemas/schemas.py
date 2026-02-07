# schemas.py
from datetime import datetime
import enum
from pydantic import BaseModel, EmailStr, Field, field_validator, StringConstraints, HttpUrl,model_validator,validator
from typing import Optional, List, Dict, Any, Annotated

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenResponse(Token):
    role: str
    redirect_path: str
    message: str
    success: bool = True

class MessageResponse(BaseModel):
    message: str
    success: bool = True
    email: Optional[str] = None
    phone: Optional[str] = None

class TokenData(BaseModel):
    user_code: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None
    permissions: Optional[List[str]] = None

# Role Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permissions: Optional[List[str]] = []

class RoleOut(RoleBase):
    id: int

    class Config:
        from_attributes = True


# ===== User Schemas =====
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str


class UserCreate(UserBase):
    password: str
    role: Optional[str] = "customer"  # Default role is customer
    
    # Optional additional fields for enhanced user creation
    pan_card_number: Optional[str] = None
    aadhaar_card_number: Optional[str] = None
    shop_name: Optional[str] = None
    scheme: Optional[str] = None
    mobile: Optional[str] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        # Only allow customer for public registration via this schema
        # Other roles should use member management system
        if v != "customer":
            raise ValueError('Public registration only supports customer role. Other roles require administrator invitation.')
        return v


class UserOut(UserBase):
    id: int
    user_code: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    role_id: int
    role_name: Optional[str] = None  # Add role name for easier access
    profile_photo: Optional[str] = None
    

    class Config:
        from_attributes = True

class UserRegisterResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserLogin(BaseModel):
    identifier: Optional[str] = None  # Can be user_code, email, or phone
    user_code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str

    @model_validator(mode="before")
    def process_identifier(cls, values):
        identifier = values.get('identifier')
        if identifier:
            # Check if it looks like an email
            if '@' in identifier:
                values['email'] = identifier
            # Check if it's a phone number (only digits)
            elif identifier.isdigit():
                values['phone'] = identifier
            # Otherwise treat as user_code
            else:
                values['user_code'] = identifier

        identifiers = [values.get('user_code'), values.get('email'), values.get('phone')]
        if not any(identifiers):
            raise ValueError('At least one identifier (user_code, email, or phone) must be provided.')
        return values


# ===== Token Schemas =====
class TokenBase(BaseModel):
    token: str
    expires_at: datetime


class TokenCreate(TokenBase):
    pass


class TokenOut(TokenBase):
    id: int
    revoked: bool

    class Config:
        from_attributes = True


# ===== Auth Schemas =====
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    role: Optional[str] = None
    permissions: Optional[List[str]] = []
    user_id: Optional[int] = None


class RefreshRequest(BaseModel):
    refresh_token: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    profile_picture_url: Optional[str] = None
    preferred_currency: Optional[str] = None
    mfa_enabled: Optional[bool] = None
    pin: str

    class Config:
        from_attributes = True



class BankAccountBase(BaseModel):
    bank_name: str
    ifsc: str
    account_holder: str
    account_number: str  # plain account number


class BankAccountCreate(BankAccountBase):
    pin: str = Field(..., min_length=6, max_length=6)


class BankAccountOut(BankAccountBase):
    id: int
    is_verified: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    security_pin: str = Field(..., min_length=4, max_length=6)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        new_password = info.data.get("new_password")
        if new_password != v:
            raise ValueError("New password and confirm password do not match")
        return v
# ============================= kyc details =========================================

AadhaarStr = Annotated[str, StringConstraints(min_length=12, max_length=12, pattern=r"^[0-9]{12}$")]
GSTINStr = Annotated[str, StringConstraints(min_length=15, max_length=15, pattern=r"^[0-9A-Z]{15}$")]

class CompanyStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    delete = "delete"

class KYCBase(BaseModel):
    pan_card_no: Optional[str] = Field(None, min_length=10, max_length=10)
    aadhar_card_no: Optional[str] = Field(None, min_length=12, max_length=12)
    profile_photo_url: Optional[str] = None
    status: Optional[str] = 'pending'

    @validator('profile_photo_url', pre=True)
    def validate_photo_url(cls, v):
        if not v:
            return None # Allow None values
        
        # 1. Basic URL format check
        try:
            HttpUrl(v)
        except ValueError:
            raise ValueError('Profile photo URL is not a valid URL.')

        # 2. File extension check
        valid_extensions = ('.jpg', '.jpeg', '.png')
        if not v.lower().endswith(valid_extensions):
            raise ValueError('Profile photo URL must be a JPG, JPEG, or PNG file.')
        
        return v

# Schema for creating/submitting KYC
class KYCCreate(KYCBase):
    pin: str = Field(..., min_length=4) 

# Schema for a full KYC record to be returned by the API
class KYCOut(KYCBase):
    id: int
    user_id: int
    submitted_at: datetime
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for updating KYC status by an admin
class KYCUpdate(BaseModel):
    # This schema is used to update the status of an existing KYC record.
    # It does not include the 'pin' as this is an internal, admin-only update.
    status: str = Field(..., pattern="^(pending|verified|rejected)$")
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class CompanyBase(BaseModel):
    company_name: str
    company_website: Optional[HttpUrl] = None
    company_sender_id: Optional[str] = None
    company_smsuser: Optional[str] = None
    company_smspassword: Optional[str] = None
    status: CompanyStatus = CompanyStatus.active

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    company_website: Optional[HttpUrl] = None
    company_sender_id: Optional[str] = None
    company_smsuser: Optional[str] = None
    company_smspassword: Optional[str] = None
    status: Optional[CompanyStatus] = None

class CompanyOut(CompanyBase):
    id: int
    added_date: datetime
    modified_date: datetime

    class Config:
        from_attributes = True

class CompanyDetailsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_fullname: Optional[str] = None
    company_website: Optional[str] = None

    class Config:
        from_attributes = True

class CompanyNewsUpdate(BaseModel):
    company_news: str
    company_bill_notice: str

    class Config:
        from_attributes = True

class CompanySupportDetailsUpdate(BaseModel):
    company_contact_no: str
    company_email: str

    class Config:
        from_attributes = True

class CompanySupportDetailsOut(BaseModel):
    id: int
    company_name: str
    company_contact_no: str
    company_email: str

    class Config:
        from_attributes = True

# WhiteLabel creation schema
class WhiteLabelCreate(BaseModel):
    name: str
    mobile: str
    email: str
    state: str
    address: str
    city: str
    pincode: str
    shop_name: str
    pancard: str
    aadhar_card: str
    company_name: str
    domain: str
    role_id: int

    class Config:
        from_attributes = True

class WhiteLabelOut(BaseModel):
    id: int
    name: str
    mobile: str
    email: str
    state: str
    address: str
    city: str
    pincode: str
    shop_name: str
    pancard: str
    aadhar_card: str
    company_name: str
    domain: str
    role_id: int

    class Config:
        from_attributes = True

# Member creation schema
class MemberCreate(BaseModel):
    name: str
    mobile: str
    email: str
    state: str
    address: str
    city: str
    pincode: str
    shop_name: str
    pancard: str
    aadhar_card: str

    class Config:
        from_attributes = True

class MemberOut(BaseModel):
    id: int
    name: str
    mobile: str
    email: str
    state: str
    address: str
    city: str
    pincode: str
    shop_name: str
    pancard: str
    aadhar_card: str

    class Config:
        from_attributes = True

# Provider schemas
class ProviderCreate(BaseModel):
    provider_name: str
    provider_type: str
    status: str
    charge_type: str

    class Config:
        from_attributes = True

class ProviderUpdate(BaseModel):
    provider_name: str | None = None
    provider_type: str | None = None
    status: str | None = None
    charge_type: str | None = None

    class Config:
        from_attributes = True

class ProviderOut(BaseModel):
    id: int
    provider_name: str
    provider_type: str
    status: str
    charge_type: str

    class Config:
        from_attributes = True
class UserRoleAssignment(BaseModel):
    user_id: Optional[int] = None
    role_id: int

class OTPRequest(BaseModel):
    identifier: str  # username, email, or phone

class OTPVerifyRequest(BaseModel):
    identifier: str  # username, email, or phone
    otp: str


class MpinLogin(BaseModel):
    identifier: str  # user_code, email, phone, or username
    mpin: str        # 4-digit MPIN
