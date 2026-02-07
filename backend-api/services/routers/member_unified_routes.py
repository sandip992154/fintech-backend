"""
Unified Member Management API Routes
Combines core and admin functionality with role-based access control
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List, Union
from enum import Enum

from database.database import get_db
from services.models.models import User, Role
from services.schemas.member_schema import (
    MemberCreateRequest, MemberCreateResponse,
    MemberOut, MemberListResponse,
    MemberUpdateRequest, MemberUpdateResponse,
    MemberStatusUpdateRequest, MemberDeleteResponse,
    RoleBasedMemberListRequest, EnhancedMemberListResponse,
    ParentSelectionResponse, UserRolePermissionsResponse, ParentSelectionOption
)
from services.schemas.member_admin_schema import (
    MemberAdminListResponse, MemberListRequest,
    MemberExportRequest, SchemeListResponse,
    LocationOptionsResponse, MemberDashboardStats,
    BulkMemberAction, BulkActionResponse
)
from services.auth.auth import get_current_user
from services.business.member_service import member_service
from services.utils.member_utils import get_manageable_roles, get_creatable_roles
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/members", tags=["Member Management"])

# ======================== Access Level Enum ========================

class AccessLevel(str, Enum):
    BASIC = "basic"           # Core functionality only
    ENHANCED = "enhanced"     # Enhanced data with some admin features
    ADMIN = "admin"          # Full administrative capabilities
    SUPER = "super"          # System-wide administrative access

# ======================== Role-Based Access Control ========================

def get_user_access_level(user_role: str) -> AccessLevel:
    """Determine user's access level based on role"""
    role_access_map = {
        # Lowercase database role names (primary)
        "super_admin": AccessLevel.SUPER,
        "admin": AccessLevel.ADMIN,
        "whitelabel": AccessLevel.ENHANCED,
        "mds": AccessLevel.ENHANCED,
        "distributor": AccessLevel.BASIC,
        "retailer": AccessLevel.BASIC,
        "customer": AccessLevel.BASIC,
        
        # Pascal case variants (backup compatibility)
        "SuperAdmin": AccessLevel.SUPER,
        "Admin": AccessLevel.ADMIN,
        "WhiteLabel": AccessLevel.ENHANCED,
        "MDS": AccessLevel.ENHANCED,
        "Distributor": AccessLevel.BASIC,
        "Retailer": AccessLevel.BASIC,
        "Customer": AccessLevel.BASIC
    }
    
    # Case-insensitive lookup with debug logging
    user_role_lower = user_role.lower() if user_role else ""
    
    # Try exact match first
    if user_role in role_access_map:
        access_level = role_access_map[user_role]
        logger.info(f"Access level for role '{user_role}': {access_level.value}")
        return access_level
    
    # Try lowercase match
    if user_role_lower in role_access_map:
        access_level = role_access_map[user_role_lower]
        logger.info(f"Access level for role '{user_role}' (matched as '{user_role_lower}'): {access_level.value}")
        return access_level
    
    # Default to basic with warning
    logger.warning(f"Unknown role '{user_role}', defaulting to BASIC access level")
    return AccessLevel.BASIC

def require_access_level(required_level: AccessLevel):
    """Decorator to enforce minimum access level"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            user_level = get_user_access_level(current_user.role.name)
            
            # Check access hierarchy: SUPER > ADMIN > ENHANCED > BASIC
            access_hierarchy = {
                AccessLevel.BASIC: 0,
                AccessLevel.ENHANCED: 1, 
                AccessLevel.ADMIN: 2,
                AccessLevel.SUPER: 3
            }
            
            if access_hierarchy[user_level] < access_hierarchy[required_level]:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Insufficient access level. Required: {required_level.value}, Current: {user_level.value}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ======================== Unified Member CRUD Operations ========================

@router.post("/create", response_model=MemberCreateResponse)
def create_member(
    member_data: MemberCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new member with role-based permissions"""
    logger.info(f"Creating member with role '{member_data.role_name}' by user '{current_user.user_code}'")
    
    member_out, email_error = member_service.create_member(member_data, current_user, db)
    
    logger.info(f"Member created successfully: {member_out.user_code} by {current_user.user_code}")
    
    return MemberCreateResponse(
        success=True,
        member=member_out,
        message="Member created successfully",
        email_sent=email_error is None,
        email_error=email_error
    )

@router.get("/list", response_model=Union[MemberListResponse, MemberAdminListResponse])
def list_members(
    # Basic parameters
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    
    # Enhanced parameters (for higher access levels)
    include_wallet_data: bool = Query(False, description="Include wallet information (requires enhanced access)"),
    include_parent_info: bool = Query(False, description="Include parent hierarchy info (requires enhanced access)"),
    include_transaction_summary: bool = Query(False, description="Include transaction summaries (requires admin access)"),
    
    # Advanced filtering (admin level)
    date_from: Optional[str] = Query(None, description="Filter from date (requires admin access)"),
    date_to: Optional[str] = Query(None, description="Filter to date (requires admin access)"),
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified member listing with role-based data access
    Returns different data based on user's access level
    """
    user_access = get_user_access_level(current_user.role.name)
    
    logger.info(f"Member list request by user '{current_user.user_code}' with role '{current_user.role.name}' (access level: {user_access.value})")
    logger.info(f"Request parameters: page={page}, limit={limit}, role={role}, include_wallet_data={include_wallet_data}, include_parent_info={include_parent_info}")
    
    # Validate enhanced features access
    if include_wallet_data and user_access not in [AccessLevel.ENHANCED, AccessLevel.ADMIN, AccessLevel.SUPER]:
        logger.warning(f"User '{current_user.user_code}' with role '{current_user.role.name}' attempted to access wallet data (access level: {user_access.value})")
        raise HTTPException(status_code=403, detail="Wallet data access requires enhanced privileges")
    
    if include_transaction_summary and user_access not in [AccessLevel.ADMIN, AccessLevel.SUPER]:
        raise HTTPException(status_code=403, detail="Transaction data access requires admin privileges")
    
    if (date_from or date_to) and user_access not in [AccessLevel.ADMIN, AccessLevel.SUPER]:
        raise HTTPException(status_code=403, detail="Date filtering requires admin privileges")
    
    logger.info(f"Listing members requested by user '{current_user.user_code}' with access level '{user_access.value}'")
    
    # Call the existing list_members method for all access levels
    # The method already handles role-based filtering internally
    member_list, total = member_service.list_members(
        current_user, db, page, limit, role, is_active, search
    )
    
    # Calculate pagination fields
    total_pages = (total + limit - 1) // limit  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    # Return appropriate response based on access level
    if user_access == AccessLevel.BASIC:
        return MemberListResponse(
            members=member_list,
            total=total,
            page=page,
            limit=limit
        )
    else:
        # Enhanced response for higher access levels
        return MemberAdminListResponse(
            members=member_list,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )

# ======================== Reference Data (Universal Access) ========================

@router.get("/schemes", response_model=SchemeListResponse)
def get_schemes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available schemes for member creation (All roles)"""
    return member_service.get_schemes(current_user, db)

@router.get("/locations", response_model=LocationOptionsResponse)
def get_locations():
    """Get available locations (states and cities) (All roles)"""
    return member_service.get_locations()

@router.get("/parents", response_model=ParentSelectionResponse)
def get_parent_options(
    role: Optional[str] = Query(None, description="Filter parents by role"),
    search: Optional[str] = Query(None, description="Search parents"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available parent options for member creation based on hierarchy (All roles)"""
    try:
        # Get manageable roles for the current user
        manageable_roles = get_manageable_roles(current_user.role_id)
        
        return member_service.get_parent_options(
            current_user=current_user,
            db=db,
            role_filter=role,
            search_query=search,
            manageable_roles=manageable_roles
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting parent options: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard", response_model=MemberDashboardStats)
@require_access_level(AccessLevel.ENHANCED)
def get_member_dashboard(
    include_financial_metrics: bool = Query(False, description="Include financial metrics (requires admin access)"),
    include_system_wide_stats: bool = Query(False, description="Include system-wide statistics (requires super access)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for member management (Enhanced+ access required)"""
    user_access = get_user_access_level(current_user.role.name)
    
    # Validate feature access
    if include_financial_metrics and user_access not in [AccessLevel.ADMIN, AccessLevel.SUPER]:
        raise HTTPException(status_code=403, detail="Financial metrics require admin privileges")
    
    if include_system_wide_stats and user_access != AccessLevel.SUPER:
        raise HTTPException(status_code=403, detail="System-wide statistics require super admin privileges")
    
    return member_service.get_dashboard_stats(
        current_user, db, 
        include_financial=include_financial_metrics,
        include_system_wide=include_system_wide_stats
    )

# ======================== Individual Member Operations ========================

@router.get("/{member_id}", response_model=MemberOut)
def get_member_details(
    member_id: int,
    include_sensitive_data: bool = Query(False, description="Include sensitive information (requires admin access)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific member with role-based data access"""
    user_access = get_user_access_level(current_user.role.name)
    
    if include_sensitive_data and user_access not in [AccessLevel.ADMIN, AccessLevel.SUPER]:
        raise HTTPException(status_code=403, detail="Sensitive data access requires admin privileges")
    
    return member_service.get_member_details(
        member_id, current_user, db, include_sensitive=include_sensitive_data
    )

@router.put("/{member_id}", response_model=MemberUpdateResponse)
def update_member(
    member_id: int,
    update_data: MemberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update member information with role-based field access"""
    member_out = member_service.update_member(member_id, update_data, current_user, db)
    
    return MemberUpdateResponse(
        member=member_out,
        message="Member updated successfully"
    )

@router.patch("/{member_id}/status", response_model=dict)
def update_member_status(
    member_id: int,
    status_data: MemberStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update member active status"""
    return member_service.update_member_status(member_id, status_data, current_user, db)

@router.delete("/{member_id}", response_model=MemberDeleteResponse)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a member (soft delete by deactivating)"""
    result = member_service.delete_member(member_id, current_user, db)
    
    return MemberDeleteResponse(
        message=result["message"],
        member_id=result["member_id"]
    )

# ======================== Advanced Operations (Role-Gated) ========================

@router.post("/bulk-action", response_model=BulkActionResponse)
@require_access_level(AccessLevel.ENHANCED)
def bulk_member_action(
    action_data: BulkMemberAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk actions on multiple members (Enhanced+ access required)"""
    user_access = get_user_access_level(current_user.role.name)
    
    # Role change operations require admin access
    if action_data.action == "change_role" and user_access not in [AccessLevel.ADMIN, AccessLevel.SUPER]:
        raise HTTPException(status_code=403, detail="Role change operations require admin privileges")
    
    return member_service.bulk_member_action(action_data, current_user, db)

@router.post("/export")
@require_access_level(AccessLevel.ENHANCED)
def export_members(
    request: MemberExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export member data in various formats (Enhanced+ access required)"""
    user_access = get_user_access_level(current_user.role.name)
    
    # Financial data export requires admin access
    if request.include_financial_data and user_access not in [AccessLevel.ADMIN, AccessLevel.SUPER]:
        raise HTTPException(status_code=403, detail="Financial data export requires admin privileges")
    
    return member_service.export_members(request, current_user, db)

@router.get("/permissions", response_model=UserRolePermissionsResponse)
def get_user_role_permissions(
    current_user: User = Depends(get_current_user)
):
    """Get current user's role permissions and manageable roles (All roles)"""
    manageable_roles = get_manageable_roles(current_user.role.name)
    creatable_roles = get_creatable_roles(current_user.role.name)
    user_access = get_user_access_level(current_user.role.name)
    
    return UserRolePermissionsResponse(
        current_role=current_user.role.name,
        manageable_roles=manageable_roles,
        creatable_roles=creatable_roles,
        can_create=len(creatable_roles) > 0,
        can_manage=len(manageable_roles) > 0,
        access_level=user_access.value
    )

@router.get("/dashboard", response_model=MemberDashboardStats)
@require_access_level(AccessLevel.ENHANCED)
def get_member_dashboard(
    include_financial_metrics: bool = Query(False, description="Include financial metrics (requires admin access)"),
    include_system_wide_stats: bool = Query(False, description="Include system-wide statistics (requires super access)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for member management (Enhanced+ access required)"""
    user_access = get_user_access_level(current_user.role.name)
    
    # Validate feature access
    if include_financial_metrics and user_access not in [AccessLevel.ADMIN, AccessLevel.SUPER]:
        raise HTTPException(status_code=403, detail="Financial metrics require admin privileges")
    
    if include_system_wide_stats and user_access != AccessLevel.SUPER:
        raise HTTPException(status_code=403, detail="System-wide statistics require super admin privileges")
    
    return member_service.get_dashboard_stats(
        current_user, db, 
        include_financial=include_financial_metrics,
        include_system_wide=include_system_wide_stats
    )

# ======================== Reference Data (Universal Access) ========================

@router.get("/schemes", response_model=SchemeListResponse)
def get_schemes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available schemes for member creation (All roles)"""
    return member_service.get_schemes(current_user, db)

@router.get("/locations", response_model=LocationOptionsResponse)
def get_locations():
    """Get available locations (states and cities) (All roles)"""
    return member_service.get_locations()

@router.get("/parents", response_model=ParentSelectionResponse)
def get_parent_options(
    role: Optional[str] = Query(None, description="Filter parents by role"),
    search: Optional[str] = Query(None, description="Search parents"),
    created_by_user: Optional[int] = Query(None, description="Filter by creator user ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available parent options for member creation based on hierarchy (All roles)"""
    try:
        logger.info(f"Fetching parents - role: {role}, current_user: {current_user.user_code}, current_role: {current_user.role.name}")
        
        # Build base query for potential parents
        query = db.query(User).join(Role)
        
        # Apply role filter - this should be the parent role (admin, whitelabel, mds, etc.)
        if role:
            query = query.filter(Role.name == role)

        # Apply created_by_user filter if provided
        if created_by_user is not None:
            query = query.filter(User.created_by == created_by_user)

        # Always filter for active users
        query = query.filter(User.is_active == True)
        
        # Hierarchy logic based on current user role and requested parent role
        current_user_role = current_user.role.name.lower()
        requested_parent_role = role.lower() if role else None
        
        logger.info(f"Current user role: {current_user_role}, Requested parent role: {requested_parent_role}")
        
        if current_user_role == "super_admin":
            # SuperAdmin can see all users of the requested role
            logger.info("SuperAdmin access - showing all users of requested role")
            pass
        elif requested_parent_role == "admin":
            # For admin parents, show admins that can be parents
            if current_user_role == "admin":
                # Admin can use themselves as parent for whitelabel creation
                query = query.filter(User.id == current_user.id)
                logger.info("Admin looking for admin parents - using self")
            else:
                # Other roles: find admins in their hierarchy
                # Start with current user's parent and traverse up
                potential_admin_ids = []
                check_user = current_user
                while check_user.parent_id:
                    parent = db.query(User).filter(User.id == check_user.parent_id).first()
                    if parent and parent.role.name.lower() == "admin":
                        potential_admin_ids.append(parent.id)
                        break  # Found admin parent
                    check_user = parent if parent else None
                    if not check_user:
                        break
                
                if potential_admin_ids:
                    query = query.filter(User.id.in_(potential_admin_ids))
                    logger.info(f"Found admin parents in hierarchy: {potential_admin_ids}")
                else:
                    query = query.filter(User.id == -1)  # No results
                    logger.info("No admin parents found in hierarchy")
        else:
            # For other parent roles, show users created under current user
            query = query.filter(User.parent_id == current_user.id)
            logger.info(f"Looking for {requested_parent_role} created by current user")
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.user_code.ilike(search_term)
                )
            )
        
        # Execute query
        potential_parents = query.order_by(User.full_name).limit(50).all()
        
        logger.info(f"Found {len(potential_parents)} potential parents")
        
        # Convert to response format
        parent_options = [
            ParentSelectionOption(
                id=parent.id,
                name=parent.full_name,
                user_code=parent.user_code,
                role_name=parent.role.name,
                email=parent.email,
                is_active=parent.is_active
            )
            for parent in potential_parents
        ]
        
        return ParentSelectionResponse(
            success=True,
            parents=parent_options,
            message=f"Found {len(parent_options)} potential parents"
        )
        
    except Exception as e:
        logger.error(f"Error fetching parent options for user {current_user.user_code}: {str(e)}")
        return ParentSelectionResponse(
            success=False,
            parents=[],
            message="Failed to fetch parent options"
        )

@router.get("/permissions", response_model=UserRolePermissionsResponse)
def get_user_role_permissions(
    current_user: User = Depends(get_current_user)
):
    """Get current user's role permissions and manageable roles (All roles)"""
    manageable_roles = get_manageable_roles(current_user.role.name)
    creatable_roles = get_creatable_roles(current_user.role.name)
    user_access = get_user_access_level(current_user.role.name)
    
    return UserRolePermissionsResponse(
        current_role=current_user.role.name,
        manageable_roles=manageable_roles,
        creatable_roles=creatable_roles,
        can_create=len(creatable_roles) > 0,
        can_manage=len(manageable_roles) > 0,
        access_level=user_access.value
    )