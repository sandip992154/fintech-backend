"""
Enhanced Member Management Schemas for Role-based User Creation and Management
"""
from pydantic import BaseModel, EmailStr, Field, validator, model_validator
from typing import Optional, List
from datetime import datetime
from config.constants import VALIDATION_PATTERNS, ROLE_HIERARCHY

# Base Member Schema with all form fields
class MemberBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the member")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., pattern=VALIDATION_PATTERNS["PHONE"], description="Phone number")
    mobile: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PHONE"], description="Alternative mobile number")
    
    # Address Information (Enhanced)
    address: str = Field(..., min_length=10, max_length=500, description="Complete address")
    pin_code: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PINCODE"], description="PIN code")
    
    # Business Information (Enhanced)
    shop_name: str = Field(..., min_length=2, max_length=255, description="Shop/Business name")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    scheme: Optional[str] = Field(None, max_length=100, description="Scheme/Plan")
    
    # KYC Information (Enhanced)
    pan_card_number: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PAN_CARD"], description="Personal PAN card number")
    company_pan_card: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PAN_CARD"], description="Company PAN card number")
    aadhaar_card_number: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["AADHAR_CARD"], description="Aadhaar card number")
    
    # Parent Selection for Hierarchy
    parent_id: Optional[int] = Field(None, description="Parent user ID in hierarchy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "9876543210",
                "mobile": "8765432109",
                "address": "123 Main Street, Sector 15, Mumbai, Maharashtra",
                "pin_code": "400001",
                "shop_name": "Doe Enterprises",
                "company_name": "ABC Technologies Pvt Ltd",
                "scheme": "Premium",
                "pan_card_number": "ABCDE1234F",
                "company_pan_card": "ABCDF5678G",
                "aadhaar_card_number": "123456789012",
                "parent_id": 1
            }
        }

# Member Creation Schema
class MemberCreateRequest(MemberBase):
    role_name: str = Field(..., description="Role name for the new member")
    password: Optional[str] = Field(None, min_length=8, description="Password for the new member (auto-generated if not provided)")
    
    @validator('role_name')
    def validate_role_name(cls, v):
        if v not in ROLE_HIERARCHY:
            raise ValueError(f"Invalid role. Must be one of: {list(ROLE_HIERARCHY.keys())}")
        return v
    
    @validator('pan_card_number')
    def validate_pan_optional(cls, v):
        if v and not v.strip():
            return None
        return v
    
    @validator('aadhaar_card_number')
    def validate_aadhaar_optional(cls, v):
        if v and not v.strip():
            return None
        return v
    
    @validator('company_pan_card')
    def validate_company_pan_optional(cls, v):
        if v and not v.strip():
            return None
        return v
    
    @model_validator(mode='after')
    def validate_parent_hierarchy(cls, values):
        """Validate parent selection based on role hierarchy"""
        role_name = values.role_name
        parent_id = values.parent_id
        
        # SuperAdmin doesn't need parent
        if role_name == "SuperAdmin":
            values.parent_id = None
        # Admin should have SuperAdmin as parent (can be auto-assigned)
        elif role_name == "Admin" and parent_id is None:
            # This will be handled in the API to auto-assign SuperAdmin
            pass
        # Other roles must have a parent
        elif role_name in ["WhiteLabel", "Distributor", "Retailer", "CustomerSupport"] and parent_id is None:
            raise ValueError(f"{role_name} must have a parent assigned")
        
        return values

# Member Update Schema
class MemberUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PHONE"])
    mobile: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PHONE"])
    
    # Address Information (Updated)
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    pin_code: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PINCODE"])
    
    # Business Information (Updated)
    shop_name: Optional[str] = Field(None, min_length=2, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    scheme: Optional[str] = Field(None, max_length=100)
    
    # KYC Information (Updated)
    pan_card_number: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PAN_CARD"])
    company_pan_card: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["PAN_CARD"])
    aadhaar_card_number: Optional[str] = Field(None, pattern=VALIDATION_PATTERNS["AADHAR_CARD"])
    
    # Parent and Status
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None

# Member Output Schema
class MemberOut(BaseModel):
    id: int
    user_code: str
    full_name: str
    email: str
    phone: str
    mobile: Optional[str] = None
    
    # Address Information (Updated)
    address: Optional[str] = None
    pin_code: Optional[str] = None
    
    # Business Information (Updated)
    shop_name: Optional[str] = None
    company_name: Optional[str] = None
    scheme: Optional[str] = None
    
    # KYC Information (Updated)
    pan_card_number: Optional[str] = None
    company_pan_card: Optional[str] = None
    aadhaar_card_number: Optional[str] = None
    
    # Hierarchy and Role Information
    role_id: int
    role: str  # Role name for compatibility
    role_name: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    
    # Status and Metadata
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Additional computed fields
    kyc_status: Optional[str] = "not_submitted"
    profile_complete: bool = False
    children_count: int = 0
    
    class Config:
        from_attributes = True

# Member List Response
class MemberListResponse(BaseModel):
    members: List[MemberOut]
    total: int
    page: int
    limit: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "members": [],
                "total": 0,
                "page": 1,
                "limit": 10
            }
        }

# Member Role Assignment Schema
class MemberRoleUpdateRequest(BaseModel):
    role: str = Field(..., description="New role to assign")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ROLE_HIERARCHY:
            raise ValueError(f'Invalid role. Must be one of: {", ".join(ROLE_HIERARCHY.keys())}')
        return v

# Member Status Update Schema
class MemberStatusUpdateRequest(BaseModel):
    is_active: bool = Field(..., description="Active status of the member")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for status change")

# Member Creation Response
class MemberCreateResponse(BaseModel):
    member: MemberOut
    message: str = "Member created successfully"
    success: bool = True

# Member Update Response
class MemberUpdateResponse(BaseModel):
    member: MemberOut
    message: str = "Member updated successfully"
    success: bool = True

# Member Deletion Response
class MemberDeleteResponse(BaseModel):
    message: str = "Member deleted successfully"
    success: bool = True
    member_id: int

# Bulk Member Operations
class BulkMemberActionRequest(BaseModel):
    member_ids: List[int] = Field(..., min_items=1, description="List of member IDs")
    action: str = Field(..., pattern="^(activate|deactivate|delete)$", description="Action to perform")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for bulk action")

class BulkMemberActionResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_members: List[dict] = []
    message: str
    success: bool = True

# Role Hierarchy Response
class RoleHierarchyResponse(BaseModel):
    role: str
    level: int
    description: str
    can_create: List[str]
    manageable_roles: List[str]

class UserRolePermissionsResponse(BaseModel):
    current_role: str
    level: int
    creatable_roles: List[str]
    manageable_roles: List[str]
    hierarchy: List[RoleHierarchyResponse]

# Member Statistics
class MemberStatsResponse(BaseModel):
    total_members: int
    active_members: int
    inactive_members: int
    role_distribution: dict
    recent_additions: int  # members added in last 7 days
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_members": 150,
                "active_members": 140,
                "inactive_members": 10,
                "role_distribution": {
                    "retailer": 100,
                    "distributor": 30,
                    "mds": 15,
                    "customer": 5
                },
                "recent_additions": 12
            }
        }

# Response Schemas
class MemberCreateResponse(BaseModel):
    success: bool = False
    message: str
    member: MemberOut
    credentials: Optional[dict] = None
    
class MemberUpdateResponse(BaseModel):
    success: bool
    message: str
    member: MemberOut

class MemberListResponse(BaseModel):
    members: List[MemberOut]
    total: int
    page: int
    limit: int
    
class MemberStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: Optional[str] = None

class MemberDeleteResponse(BaseModel):
    success: bool
    message: str
    member_id: int

# Enhanced Schemas for Role-based Management
class ParentSelectionOption(BaseModel):
    """Schema for parent selection dropdown options"""
    id: int
    name: str
    user_code: str
    role_name: str
    email: str
    is_active: bool

class ParentSelectionResponse(BaseModel):
    """Response for getting available parents for a role"""
    success: bool
    parents: List[ParentSelectionOption]
    message: Optional[str] = None

class RoleBasedMemberListRequest(BaseModel):
    """Request schema for role-based member listing with filters"""
    requesting_role: str = Field(..., description="Role of the user making the request")
    requesting_user_id: int = Field(..., description="ID of the user making the request")
    
    # Filters
    role_filter: Optional[str] = Field(None, description="Filter by specific role")
    search_query: Optional[str] = Field(None, description="Search in name, email, phone")
    status_filter: Optional[str] = Field(None, description="active, inactive, all")
    parent_filter: Optional[int] = Field(None, description="Filter by parent ID")
    scheme_filter: Optional[str] = Field(None, description="Filter by scheme")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="asc or desc")

class EnhancedMemberListResponse(BaseModel):
    """Enhanced response for role-based member listing"""
    success: bool
    members: List[MemberOut]
    total: int
    page: int
    limit: int
    filters_applied: dict
    requesting_user_context: dict
    hierarchy_info: Optional[dict] = None
    message: Optional[str] = None