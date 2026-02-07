"""
Member Management Admin API Routes
Advanced admin features and bulk operations
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List

from database.database import get_db
from services.models.models import User, Role
from services.schemas.member_admin_schema import (
    MemberAdminListResponse, MemberListRequest,
    MemberExportRequest, SchemeListResponse,
    LocationOptionsResponse, MemberDashboardStats,
    BulkMemberAction, BulkActionResponse
)
from services.schemas.member_schema import (
    RoleBasedMemberListRequest, EnhancedMemberListResponse,
    ParentSelectionResponse, UserRolePermissionsResponse, ParentSelectionOption
)
from services.auth.auth import get_current_user
from services.utils.member_utils import get_manageable_roles, get_creatable_roles
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/members/admin", tags=["Member Admin"])

# ======================== Enhanced Listing and Filtering ========================

@router.post("/list", response_model=MemberAdminListResponse)
def list_members_admin(
    request: MemberListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enhanced member listing for admin panel with advanced filters"""
    # TODO: Implement admin listing logic with enhanced features
    # This would include wallet details, parent info, etc.
    pass

@router.post("/list/role-based", response_model=EnhancedMemberListResponse)
def get_role_based_member_list(
    request: RoleBasedMemberListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enhanced role-based member listing with filters"""
    # TODO: Implement role-based listing logic
    pass

# ======================== Bulk Operations ========================

@router.post("/bulk-action", response_model=BulkActionResponse)
def bulk_member_action(
    action_data: BulkMemberAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk actions on multiple members"""
    # TODO: Implement bulk operations (activate, deactivate, etc.)
    pass

# ======================== Export and Reports ========================

@router.post("/export")
def export_members(
    request: MemberExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export member data in various formats"""
    # TODO: Implement export functionality
    pass

# ======================== Dashboard and Statistics ========================

@router.get("/dashboard", response_model=MemberDashboardStats)
def get_member_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for member management"""
    # TODO: Implement dashboard statistics
    pass

# ======================== Reference Data ========================

@router.get("/schemes", response_model=SchemeListResponse)
def get_schemes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available schemes for member creation"""
    # TODO: Implement scheme listing
    pass

@router.get("/locations", response_model=LocationOptionsResponse)
def get_locations():
    """Get available locations (states and cities)"""
    # TODO: Implement location data
    pass

@router.get("/parents", response_model=ParentSelectionResponse)
def get_parent_options(
    role: Optional[str] = Query(None, description="Filter parents by role"),
    search: Optional[str] = Query(None, description="Search parents"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available parent options for member creation based on hierarchy"""
    try:
        # Get manageable roles for the current user
        manageable_roles = get_manageable_roles(current_user.role.name)
        
        # Build query for potential parents
        query = db.query(User).join(Role)
        
        # SuperAdmin can see all users as potential parents
        if current_user.role.name == "SuperAdmin":
            query = query.filter(User.is_active == True)
        else:
            # Other users can only see users in their hierarchy
            query = query.filter(
                or_(
                    User.id == current_user.id,  # Self as parent
                    User.parent_id == current_user.id,  # Direct children
                    User.id == current_user.parent_id  # Own parent
                )
            ).filter(User.is_active == True)
        
        # Apply role filter if provided
        if role:
            query = query.filter(Role.name == role)
        
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

# ======================== Role and Permission Management ========================

@router.get("/permissions", response_model=UserRolePermissionsResponse)
def get_user_role_permissions(
    current_user: User = Depends(get_current_user)
):
    """Get current user's role permissions and manageable roles"""
    manageable_roles = get_manageable_roles(current_user.role.name)
    creatable_roles = get_creatable_roles(current_user.role.name)
    
    return UserRolePermissionsResponse(
        current_role=current_user.role.name,
        manageable_roles=manageable_roles,
        creatable_roles=creatable_roles,
        can_create=len(creatable_roles) > 0,
        can_manage=len(manageable_roles) > 0
    )