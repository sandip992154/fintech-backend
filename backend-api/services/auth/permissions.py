from enum import Enum
from typing import List, Dict
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from services.models.models import User, Role
from database.database import get_db

class PortalPermission(str, Enum):
    # User Management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # Financial
    MANAGE_WALLET = "manage_wallet"
    VIEW_WALLET = "view_wallet"
    TRANSFER_FUNDS = "transfer_funds"
    
    # Services
    MANAGE_SERVICES = "manage_services"
    VIEW_SERVICES = "view_services"
    USE_SERVICES = "use_services"
    
    # Additional Services
    USE_AEPS = "use_aeps"
    USE_MATM = "use_matm"
    USE_INSURANCE = "use_insurance"
    USE_PANCARD = "use_pancard"
    USE_FASTAG = "use_fastag"
    
    # Commission
    MANAGE_COMMISSION = "manage_commission"
    VIEW_COMMISSION = "view_commission"
    
    # Reports
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"
    
    # Settings
    MANAGE_SETTINGS = "manage_settings"
    VIEW_SETTINGS = "view_settings"

class RolePermissions:
    _permissions: Dict[str, List[PortalPermission]] = {
        "superadmin": [p for p in PortalPermission],  # All permissions
        
        "admin": [
            PortalPermission.MANAGE_USERS,
            PortalPermission.VIEW_USERS,
            PortalPermission.MANAGE_WALLET,
            PortalPermission.VIEW_WALLET,
            PortalPermission.TRANSFER_FUNDS,
            PortalPermission.MANAGE_SERVICES,
            PortalPermission.VIEW_SERVICES,
            PortalPermission.MANAGE_COMMISSION,
            PortalPermission.VIEW_COMMISSION,
            PortalPermission.VIEW_REPORTS,
            PortalPermission.EXPORT_REPORTS,
            PortalPermission.VIEW_SETTINGS
        ],
        
        "whitelabel": [
            PortalPermission.MANAGE_USERS,
            PortalPermission.VIEW_USERS,
            PortalPermission.VIEW_WALLET,
            PortalPermission.TRANSFER_FUNDS,
            PortalPermission.VIEW_SERVICES,
            PortalPermission.VIEW_COMMISSION,
            PortalPermission.VIEW_REPORTS,
            PortalPermission.EXPORT_REPORTS,
            PortalPermission.VIEW_SETTINGS
        ],
        
        "master_distributor": [
            PortalPermission.MANAGE_USERS,
            PortalPermission.VIEW_USERS,
            PortalPermission.VIEW_WALLET,
            PortalPermission.TRANSFER_FUNDS,
            PortalPermission.VIEW_SERVICES,
            PortalPermission.VIEW_COMMISSION,
            PortalPermission.VIEW_REPORTS
        ],
        
        "distributor": [
            PortalPermission.MANAGE_USERS,
            PortalPermission.VIEW_USERS,
            PortalPermission.VIEW_WALLET,
            PortalPermission.TRANSFER_FUNDS,
            PortalPermission.VIEW_SERVICES,
            PortalPermission.VIEW_COMMISSION,
            PortalPermission.VIEW_REPORTS
        ],
        
        "retailer": [
            PortalPermission.VIEW_WALLET,
            PortalPermission.USE_SERVICES,
            PortalPermission.VIEW_COMMISSION,
            PortalPermission.VIEW_REPORTS
        ],
        
        "customer": [
            PortalPermission.VIEW_WALLET,
            PortalPermission.USE_SERVICES,
            PortalPermission.VIEW_REPORTS
        ]
    }
    
    @classmethod
    def get_permissions(cls, role_name: str) -> List[PortalPermission]:
        return cls._permissions.get(role_name, [])
    
    @classmethod
    def has_permission(cls, role_name: str, permission: PortalPermission) -> bool:
        return permission in cls.get_permissions(role_name)

def check_permission(required_permission: PortalPermission):
    def permission_dependency(
        user_id: int,
        db: Session = Depends(get_db)
    ):
        user = db.query(User).join(Role).filter(User.id == user_id).first()
        if not user or not user.role:
            raise HTTPException(
                status_code=404,
                detail="User or role not found"
            )
            
        if not RolePermissions.has_permission(user.role.name, required_permission):
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )
        
        return user
    
    return permission_dependency
