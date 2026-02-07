"""
Enhanced Member Management Schemas for Frontend Integration
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from config.constants import VALIDATION_PATTERNS, ROLE_HIERARCHY

# Enhanced Member Output Schema for Admin List
class MemberAdminListOut(BaseModel):
    id: int
    user_code: str
    full_name: str
    email: str
    phone: str
    mobile: Optional[str] = None
    role: str
    role_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Parent Information
    parent_details: Optional[Dict[str, Any]] = None
    
    # Company/Business Information
    company_profile: Optional[Dict[str, Any]] = None
    
    # Wallet Information
    wallet_details: Optional[Dict[str, Any]] = None
    
    # ID Stock (for display)
    id_stock: Optional[Dict[str, Any]] = None
    
    # Additional status info
    status: str = "active"  # active, inactive, suspended
    
    class Config:
        from_attributes = True

# Enhanced Member List Request with filters
class MemberListRequest(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")
    
    # Date filters
    from_date: Optional[datetime] = Field(None, description="Filter from date")
    to_date: Optional[datetime] = Field(None, description="Filter to date")
    
    # Search and filters
    search_value: Optional[str] = Field(None, description="Search by name, email, phone, or user_code")
    agent_parent: Optional[str] = Field(None, description="Filter by parent/agent")
    status: Optional[str] = Field(None, description="Filter by status")
    role: Optional[str] = Field(None, description="Filter by role")
    
    # Additional filters
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    kyc_status: Optional[str] = Field(None, description="Filter by KYC status")

# Enhanced Member List Response
class MemberAdminListResponse(BaseModel):
    members: List[MemberAdminListOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    # Summary stats
    summary: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "members": [],
                "total": 0,
                "page": 1,
                "limit": 10,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False,
                "summary": {
                    "total_active": 0,
                    "total_inactive": 0,
                    "total_wallet_balance": 0
                }
            }
        }

# Export Request Schema
class MemberExportRequest(BaseModel):
    format: str = Field("excel", description="Export format: excel, csv, pdf")
    filters: Optional[MemberListRequest] = None
    columns: Optional[List[str]] = Field(None, description="Specific columns to export")
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['excel', 'csv', 'pdf']:
            raise ValueError('Format must be excel, csv, or pdf')
        return v

# Scheme Options Schema
class SchemeOption(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    commission_rate: Optional[float] = None
    is_active: bool = True

class SchemeListResponse(BaseModel):
    schemes: List[SchemeOption]
    total: int

# State and City Options
class StateOption(BaseModel):
    id: str
    name: str
    code: Optional[str] = None

class CityOption(BaseModel):
    id: str
    name: str
    state_id: str

class LocationOptionsResponse(BaseModel):
    states: List[StateOption]
    cities: List[CityOption] = []

# Dashboard Stats for Member Management
class MemberDashboardStats(BaseModel):
    total_members: int
    active_members: int
    inactive_members: int
    pending_kyc: int
    completed_kyc: int
    
    # Role wise distribution
    role_distribution: Dict[str, int]
    
    # Recent activity
    recent_registrations: int  # Last 7 days
    recent_activations: int    # Last 7 days
    
    # Wallet summary
    total_wallet_balance: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_members": 150,
                "active_members": 140,
                "inactive_members": 10,
                "pending_kyc": 25,
                "completed_kyc": 125,
                "role_distribution": {
                    "admin": 2,
                    "distributor": 15,
                    "retailer": 80,
                    "customer": 53
                },
                "recent_registrations": 12,
                "recent_activations": 8,
                "total_wallet_balance": 150000.50
            }
        }

# Bulk operations
class BulkMemberAction(BaseModel):
    member_ids: List[int] = Field(..., min_items=1)
    action: str = Field(..., description="activate, deactivate, delete, export")
    reason: Optional[str] = None
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['activate', 'deactivate', 'delete', 'export']:
            raise ValueError('Action must be activate, deactivate, delete, or export')
        return v

class BulkActionResponse(BaseModel):
    success: bool
    message: str
    processed_count: int
    failed_count: int
    failed_items: List[Dict[str, Any]] = []