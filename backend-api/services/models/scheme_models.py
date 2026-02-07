"""
Scheme and Commission Management Database Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from database.database import Base
from .models import User, Role  # Import existing User and Role models
import enum
from typing import Optional, List


class ServiceTypeEnum(str, enum.Enum):
    """Service types supported by the platform"""
    MOBILE_RECHARGE = "mobile_recharge"
    DTH_RECHARGE = "dth_recharge"
    BILL_PAYMENTS = "bill_payments"
    AEPS = "aeps"
    DMT = "dmt"
    MICRO_ATM = "micro_atm"


class CommissionTypeEnum(str, enum.Enum):
    """Commission calculation types"""
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    SLAB_BASED = "slab_based"


class RoleEnum(str, enum.Enum):
    """Role hierarchy for commission structure"""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    WHITELABEL = "whitelabel"
    MASTERDISTRIBUTOR = "masterdistributor"
    DISTRIBUTOR = "distributor"
    RETAILER = "retailer"
    CUSTOMER = "customer"


class Scheme(Base):
    """Scheme model for managing commission schemes with user-based ownership"""
    __tablename__ = "schemes"
    
    # Define columns as they exist in the REMOTE database
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User-based ownership and hierarchy control
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Updated to match migration
    created_by_role = Column(String(50), nullable=False)  # Updated to match migration
    
    # Note: shared_with_users and shared_with_roles columns have been removed from database
    # Keep them commented out for now as they cause SQL errors
    # shared_with_users = Column(JSON, nullable=True)  # From migration
    # shared_with_roles = Column(JSON, nullable=True)  # From migration

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    owner = relationship("User", foreign_keys=[owner_id])
    commissions = relationship("Commission", back_populates="scheme", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Scheme(id={self.id}, name='{self.name}', owner_id={self.owner_id}, created_by_role='{self.created_by_role}')>"
    
    def can_be_accessed_by_user(self, user_id: int, user_role: str) -> bool:
        """Check if a user can access this scheme based on ownership and permissions"""
        from services.utils.role_hierarchy import RoleHierarchy
        
        # Owner can always access
        if self.owner_id == user_id:
            return True
            
        # Creator can always access
        if self.created_by == user_id:
            return True
            
        # Higher hierarchy roles can access (super_admin, admin can access all)
        if RoleHierarchy.can_manage_role(user_role, self.created_by_role):
            return True
            
        return False
    
    def can_be_edited_by_user(self, user_id: int, user_role: str) -> bool:
        """Check if a user can edit this scheme"""
        from services.utils.role_hierarchy import RoleHierarchy
        
        # Owner can edit
        if self.owner_id == user_id:
            return True
            
        # Creator can edit
        if self.created_by == user_id:
            return True
            
        # Higher hierarchy roles can edit
        if RoleHierarchy.can_manage_role(user_role, self.created_by_role):
            return True
            
        return False
    
    def can_be_deleted_by_user(self, user_id: int, user_role: str) -> bool:
        """Check if a user can delete this scheme"""
        from services.utils.role_hierarchy import RoleHierarchy
        
        # Creator can delete
        if self.created_by == user_id:
            return True
            
        # Only super_admin and admin roles can delete schemes they didn't create
        role_level = RoleHierarchy.get_role_level(user_role)
        if role_level <= 1:  # super_admin (0) or admin (1)
            return True
            
        return False
    
    def transfer_ownership(self, new_owner_id: int) -> bool:
        """Transfer ownership of the scheme to another user"""
        self.owner_id = new_owner_id
        self.updated_at = datetime.utcnow()
        return True


class ServiceOperator(Base):
    """Service operators for each service type"""
    __tablename__ = "service_operators"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    service_type = Column(ENUM('mobile_recharge', 'dth_recharge', 'bill_payments', 'aeps', 'dmt', 'micro_atm', name="servicetypeenum"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    commissions = relationship("Commission", back_populates="operator")

    def __repr__(self):
        return f"<ServiceOperator(id={self.id}, name='{self.name}', service='{self.service_type}')>"


class Commission(Base):
    """Commission structure for each scheme, service, and operator"""
    __tablename__ = "commissions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("service_operators.id"), nullable=False)
    service_type = Column(ENUM('mobile_recharge', 'dth_recharge', 'bill_payments', 'aeps', 'dmt', 'micro_atm', name="servicetypeenum"), nullable=False)
    commission_type = Column(ENUM('percentage', 'fixed', 'slab_based', name="commissiontypeenum"), nullable=False)
    
    # Role-wise commission values
    superadmin = Column(Float, default=0.0)
    admin = Column(Float, default=0.0)
    whitelabel = Column(Float, default=0.0)
    masterdistributor = Column(Float, default=0.0)
    distributor = Column(Float, default=0.0)
    retailer = Column(Float, default=0.0)
    customer = Column(Float, default=0.0)
    
    # For AEPS slab-based commissions
    slab_min = Column(Float, nullable=True)  # Minimum amount for this slab
    slab_max = Column(Float, nullable=True)  # Maximum amount for this slab
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    scheme = relationship("Scheme", back_populates="commissions")
    operator = relationship("ServiceOperator", back_populates="commissions")
    slabs = relationship("CommissionSlab", back_populates="commission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Commission(id={self.id}, scheme_id={self.scheme_id}, operator_id={self.operator_id})>"

    def get_commission_for_role(self, role: str) -> float:
        """Get commission value for a specific role"""
        role_mapping = {
            "superadmin": self.superadmin,
            "admin": self.admin,
            "whitelabel": self.whitelabel,
            "masterdistributor": self.masterdistributor,
            "distributor": self.distributor,
            "retailer": self.retailer,
            "customer": self.customer,
        }
        return role_mapping.get(role.lower(), 0.0)

    def validate_hierarchy(self) -> bool:
        """Validate that parent role commission >= child role commission"""
        from services.utils.role_hierarchy import RoleHierarchy
        
        commission_data = {
            "superadmin": self.superadmin,
            "admin": self.admin,
            "whitelabel": self.whitelabel,
            "masterdistributor": self.masterdistributor,
            "distributor": self.distributor,
            "retailer": self.retailer,
            "customer": self.customer
        }
        
        return RoleHierarchy.validate_commission_hierarchy(commission_data)

    def validate_positive_values(self) -> bool:
        """Validate that all commission values are non-negative"""
        values = [
            self.superadmin, self.admin, self.whitelabel,
            self.masterdistributor, self.distributor, self.retailer, self.customer
        ]
        return all(value >= 0 for value in values if value is not None)
    
    def can_edit_commission_field(self, user_role: str, field_name: str) -> bool:
        """Check if user role can edit specific commission field"""
        from services.utils.role_hierarchy import RoleHierarchy
        
        editable_fields = RoleHierarchy.get_commission_fields(user_role)
        return field_name in editable_fields
    
    def get_editable_fields_for_role(self, user_role: str) -> List[str]:
        """Get list of commission fields that user role can edit"""
        from services.utils.role_hierarchy import RoleHierarchy
        
        return RoleHierarchy.get_commission_fields(user_role)


class CommissionSlab(Base):
    """AEPS Commission slabs for amount-based commission calculation"""
    __tablename__ = "commission_slabs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(Integer, ForeignKey("commissions.id"), nullable=False)
    slab_min = Column(Float, nullable=False)
    slab_max = Column(Float, nullable=False)
    
    # Role-wise commission values for this slab
    superadmin = Column(Float, default=0.0)
    admin = Column(Float, default=0.0)
    whitelabel = Column(Float, default=0.0)
    masterdistributor = Column(Float, default=0.0)
    distributor = Column(Float, default=0.0)
    retailer = Column(Float, default=0.0)
    customer = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    commission = relationship("Commission", back_populates="slabs")

    def __repr__(self):
        return f"<CommissionSlab(id={self.id}, range={self.slab_min}-{self.slab_max})>"

    def validate_slab_range(self) -> bool:
        """Validate that slab_min < slab_max"""
        return self.slab_min < self.slab_max

    def get_commission_for_role(self, role: str) -> float:
        """Get commission value for a specific role in this slab"""
        role_mapping = {
            "superadmin": self.superadmin,
            "admin": self.admin,
            "whitelabel": self.whitelabel,
            "masterdistributor": self.masterdistributor,
            "distributor": self.distributor,
            "retailer": self.retailer,
            "customer": self.customer,
        }
        return role_mapping.get(role.lower(), 0.0)