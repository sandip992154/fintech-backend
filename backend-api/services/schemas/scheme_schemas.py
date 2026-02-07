"""
Pydantic schemas for Scheme and Commission Management
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from enum import Enum


class ServiceTypeEnum(str, Enum):
    """Service types supported by the platform"""
    MOBILE_RECHARGE = "mobile_recharge"
    DTH_RECHARGE = "dth_recharge"
    BILL_PAYMENTS = "bill_payments"
    AEPS = "aeps"
    DMT = "dmt"
    MICRO_ATM = "micro_atm"


class CommissionTypeEnum(str, Enum):
    """Commission calculation types"""
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class RoleEnum(str, Enum):
    """Role hierarchy for commission structure"""
    ADMIN = "admin"
    WHITELABEL = "whitelabel"
    MASTERDISTRIBUTOR = "masterdistributor"
    DISTRIBUTOR = "distributor"
    RETAILER = "retailer"
    CUSTOMER = "customer"


# =============================================================================
# Scheme Schemas
# =============================================================================

class SchemeBase(BaseModel):
    """Base scheme schema"""
    name: str = Field(..., min_length=3, max_length=100, description="Scheme name")
    description: Optional[str] = Field(None, max_length=500, description="Scheme description")


class SchemeCreate(SchemeBase):
    """Schema for creating a new scheme"""
    pass


class SchemeUpdate(BaseModel):
    """Schema for updating an existing scheme"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = Field(None, description="Scheme active status")


class SchemeStatusUpdate(BaseModel):
    """Schema for updating scheme status"""
    is_active: bool = Field(..., description="Scheme active status")


class SchemeOut(SchemeBase):
    """Schema for scheme output with ownership information"""
    id: int
    is_active: bool
    created_by: int
    owner_id: int  # Required field as per migration
    created_by_role: str  # Required field as per migration
    # Note: shared_with_users and shared_with_roles removed to match database schema
    # shared_with_users: Optional[List[int]] = None
    # shared_with_roles: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchemeDetailOut(SchemeOut):
    """Detailed scheme output with commission count"""
    commission_count: int = 0
    services_count: int = 0


class SchemeOwnershipTransfer(BaseModel):
    """Schema for transferring scheme ownership"""
    new_owner_id: int = Field(..., description="ID of the new owner")


class SchemeUserShare(BaseModel):
    """Schema for sharing scheme with user"""
    target_user_id: int = Field(..., description="ID of user to share with")


class SchemeRoleShare(BaseModel):
    """Schema for sharing scheme with role"""
    target_role: str = Field(..., description="Role name to share with")


# =============================================================================
# Service Operator Schemas
# =============================================================================

class ServiceOperatorBase(BaseModel):
    """Base service operator schema"""
    name: str = Field(..., min_length=2, max_length=100, description="Operator name")
    service_type: ServiceTypeEnum = Field(..., description="Service type")


class ServiceOperatorCreate(ServiceOperatorBase):
    """Schema for creating a new service operator"""
    pass


class ServiceOperatorUpdate(BaseModel):
    """Schema for updating an existing service operator"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    service_type: Optional[ServiceTypeEnum] = None
    is_active: Optional[bool] = None


class ServiceOperatorOut(ServiceOperatorBase):
    """Schema for service operator output"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Commission Schemas
# =============================================================================

class RoleCommissionValues(BaseModel):
    """Role-wise commission values"""
    admin: float = Field(0.0, ge=0, description="Admin commission")
    whitelabel: float = Field(0.0, ge=0, description="Whitelabel commission")
    masterdistributor: float = Field(0.0, ge=0, description="Master distributor commission")
    distributor: float = Field(0.0, ge=0, description="Distributor commission")
    retailer: float = Field(0.0, ge=0, description="Retailer commission")
    customer: float = Field(0.0, ge=0, description="Customer commission")

    @validator('admin', 'whitelabel', 'masterdistributor', 'distributor', 'retailer', 'customer', pre=True)
    def validate_non_negative(cls, v):
        """Ensure all commission values are non-negative"""
        if v is not None and v < 0:
            raise ValueError('Commission values must be non-negative')
        return v

    def validate_hierarchy(self) -> bool:
        """Validate commission hierarchy: parent >= child"""
        hierarchy = [
            self.admin, self.whitelabel,
            self.masterdistributor, self.distributor, self.retailer, self.customer
        ]
        
        for i in range(len(hierarchy) - 1):
            if hierarchy[i] < hierarchy[i + 1]:
                return False
        return True


class CommissionSlabBase(BaseModel):
    """Base commission slab schema"""
    slab_min: float = Field(..., ge=0, description="Minimum amount for slab")
    slab_max: float = Field(..., gt=0, description="Maximum amount for slab")

    @validator('slab_max')
    def validate_slab_range(cls, v, values):
        """Validate that slab_max > slab_min"""
        if 'slab_min' in values and v <= values['slab_min']:
            raise ValueError('slab_max must be greater than slab_min')
        return v


class CommissionSlabCreate(CommissionSlabBase, RoleCommissionValues):
    """Schema for creating commission slab"""
    pass


class CommissionSlabCreateAPI(CommissionSlabBase, RoleCommissionValues):
    """Schema for creating commission slab via API (includes commission_id)"""
    commission_id: int = Field(..., description="Commission ID for the slab")


class CommissionSlabOut(CommissionSlabBase, RoleCommissionValues):
    """Schema for commission slab output"""
    id: int
    commission_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommissionBase(BaseModel):
    """Base commission schema"""
    operator_id: int = Field(..., description="Service operator ID")
    service_type: ServiceTypeEnum = Field(..., description="Service type")
    commission_type: CommissionTypeEnum = Field(..., description="Commission type")


class CommissionCreate(CommissionBase, RoleCommissionValues):
    """Schema for creating commission"""
    # For AEPS slab-based commissions
    slab_min: Optional[float] = Field(None, ge=0, description="Minimum amount for AEPS slab")
    slab_max: Optional[float] = Field(None, gt=0, description="Maximum amount for AEPS slab")
    slabs: Optional[List[CommissionSlabCreate]] = Field(None, description="AEPS commission slabs")

    @validator('slabs')
    def validate_aeps_slabs(cls, v, values):
        """Validate AEPS slabs if service_type is AEPS"""
        if values.get('service_type') == ServiceTypeEnum.AEPS and v is not None:
            if len(v) == 0:
                # Allow empty slabs for AEPS - slabs can be added later via slab manager
                return v
            
            # Check for overlapping slabs if slabs are provided
            sorted_slabs = sorted(v, key=lambda x: x.slab_min)
            for i in range(len(sorted_slabs) - 1):
                if sorted_slabs[i].slab_max >= sorted_slabs[i + 1].slab_min:
                    raise ValueError('AEPS slabs must not overlap')
        
        return v


class CommissionUpdate(BaseModel):
    """Schema for updating commission"""
    commission_type: Optional[CommissionTypeEnum] = None
    admin: Optional[float] = Field(None, ge=0)
    whitelabel: Optional[float] = Field(None, ge=0)
    masterdistributor: Optional[float] = Field(None, ge=0)
    distributor: Optional[float] = Field(None, ge=0)
    retailer: Optional[float] = Field(None, ge=0)
    customer: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CommissionOut(CommissionBase, RoleCommissionValues):
    """Schema for commission output"""
    id: int
    scheme_id: int
    slab_min: Optional[float] = None
    slab_max: Optional[float] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Nested objects
    operator: Optional[ServiceOperatorOut] = None
    slabs: Optional[List[CommissionSlabOut]] = None

    class Config:
        from_attributes = True


# =============================================================================
# Bulk Commission Schemas
# =============================================================================

class CommissionEntry(BaseModel):
    """Single commission entry for bulk operations"""
    operator: str = Field(..., description="Operator name")
    commission_type: CommissionTypeEnum = Field(..., description="Commission type")
    whitelabel: float = Field(..., ge=0, description="Whitelabel commission")
    masterdistributor: float = Field(..., ge=0, description="Master distributor commission")
    distributor: float = Field(..., ge=0, description="Distributor commission")
    retailer: float = Field(..., ge=0, description="Retailer commission")
    admin: Optional[float] = Field(0.0, ge=0, description="Admin commission")
    customer: Optional[float] = Field(0.0, ge=0, description="Customer commission")


class AEPSCommissionSlab(BaseModel):
    """AEPS commission slab for bulk operations"""
    slab_min: float = Field(..., ge=0, description="Minimum amount")
    slab_max: float = Field(..., gt=0, description="Maximum amount")
    whitelabel: float = Field(..., ge=0, description="Whitelabel commission")
    md: float = Field(..., ge=0, description="Master distributor commission")
    distributor: float = Field(..., ge=0, description="Distributor commission")
    retailer: float = Field(..., ge=0, description="Retailer commission")
    admin: Optional[float] = Field(0.0, ge=0, description="Admin commission")
    customer: Optional[float] = Field(0.0, ge=0, description="Customer commission")


class AEPSCommissionEntry(BaseModel):
    """AEPS commission entry with slabs"""
    operator: str = Field(..., description="Operator name")
    commission_type: CommissionTypeEnum = Field(..., description="Commission type")
    slabs: List[AEPSCommissionSlab] = Field(..., min_items=1, description="Commission slabs")


class BulkCommissionCreate(BaseModel):
    """Schema for bulk commission creation"""
    service: ServiceTypeEnum = Field(..., description="Service type")
    entries: List[Union[CommissionEntry, AEPSCommissionEntry]] = Field(
        ..., min_items=1, description="Commission entries"
    )


class BulkCommissionResponse(BaseModel):
    """Response for bulk commission operations"""
    service: ServiceTypeEnum
    total_entries: int
    successful_entries: int
    failed_entries: int
    errors: List[str] = []


# =============================================================================
# Export/Import Schemas
# =============================================================================

class CommissionExportRow(BaseModel):
    """Single row for commission export"""
    operator: str
    service_type: str
    commission_type: str
    whitelabel: float
    masterdistributor: float
    distributor: float
    retailer: float
    admin: Optional[float] = None
    customer: Optional[float] = None
    slab_min: Optional[float] = None
    slab_max: Optional[float] = None


class CommissionExportData(BaseModel):
    """Commission export data"""
    scheme_name: str
    service_type: ServiceTypeEnum
    export_date: datetime
    total_entries: int
    data: List[CommissionExportRow]


# =============================================================================
# Response Schemas
# =============================================================================

class StandardResponse(BaseModel):
    """Standard API response"""
    success: bool = True
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """Paginated response schema"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


class CommissionListResponse(BaseModel):
    """Response for commission listing by service"""
    service: ServiceTypeEnum
    entries: List[CommissionOut]


class SchemeCommissionSummary(BaseModel):
    """Summary of commissions for a scheme"""
    scheme_id: int
    scheme_name: str
    total_commissions: int
    services: List[str]
    last_updated: datetime