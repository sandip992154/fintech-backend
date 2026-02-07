"""
API Routes for Scheme Management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database.database import get_db
from services.auth.auth import get_current_user
from services.models.models import User
from services.models.scheme_models import Commission
from services.business.scheme_service import SchemeService
from services.schemas.scheme_schemas import (
    SchemeCreate, SchemeUpdate, SchemeStatusUpdate, SchemeOut, SchemeDetailOut,
    StandardResponse, PaginatedResponse
)
from config.role_manager import RoleManager


router = APIRouter(prefix="/schemes", tags=["Scheme Management"])


def check_scheme_permissions(current_user: User, action: str):
    """Check if user has permissions for scheme operations"""
    from services.utils.role_hierarchy import RoleHierarchy
    
    user_role = current_user.role.name.lower()
    permissions = RoleHierarchy.get_role_permissions(user_role)
    
    permission_map = {
        "create": "schemes.create",
        "update": "schemes.update", 
        "delete": "schemes.delete",
        "read": True  # All authenticated users can read
    }
    
    required_permission = permission_map.get(action)
    if required_permission is True:
        return True
        
    if required_permission and not permissions.get(required_permission, False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. User role '{user_role}' cannot {action} schemes."
        )


@router.post("", response_model=SchemeOut, status_code=status.HTTP_201_CREATED)
async def create_scheme(
    scheme_data: SchemeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new scheme with user-based ownership.
    
    **Permissions**: SuperAdmin, Admin, WhiteLabel
    """
    check_scheme_permissions(current_user, "create")
    
    scheme_service = SchemeService(db)
    user_role = current_user.role.name.lower()
    scheme = scheme_service.create_scheme(
        scheme_data=scheme_data, 
        created_by=current_user.id, 
        creator_role=user_role,
        owner_id=current_user.id  # Set owner_id explicitly
    )
    
    return SchemeOut.model_validate(scheme)


@router.get("", response_model=PaginatedResponse)
async def list_schemes(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of schemes with user-based filtering.
    
    **Permissions**: All authenticated users (filtered by ownership)
    """
    check_scheme_permissions(current_user, "read")
    
    scheme_service = SchemeService(db)
    skip = (page - 1) * size
    user_role = current_user.role.name.lower()
    
    schemes, total = scheme_service.get_schemes(
        skip=skip,
        limit=size,
        is_active=is_active,
        search=search,
        current_user_id=current_user.id,
        current_user_role=user_role
    )
    
    # Convert SQLAlchemy models to Pydantic models
    scheme_items = [SchemeOut.model_validate(scheme) for scheme in schemes]
    
    # Calculate pagination info
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=scheme_items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{scheme_id}", response_model=SchemeDetailOut)
async def get_scheme(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific scheme by ID with detailed information.
    
    **Permissions**: All authenticated users
    """
    check_scheme_permissions(current_user, "read")
    
    scheme_service = SchemeService(db)
    scheme = scheme_service.get_scheme_by_id(scheme_id)
    
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found"
        )
    
    # Get additional details
    commission_count = db.query(Commission).filter(
        Commission.scheme_id == scheme_id
    ).count()
    
    services_count = db.query(Commission.service_type).filter(
        Commission.scheme_id == scheme_id
    ).distinct().count()
    
    # Convert to detailed response
    scheme_detail = SchemeDetailOut(
        **scheme.__dict__,
        commission_count=commission_count,
        services_count=services_count
    )
    
    return scheme_detail


@router.put("/{scheme_id}", response_model=SchemeOut)
async def update_scheme(
    scheme_id: int,
    scheme_data: SchemeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing scheme.
    
    **Permissions**: SuperAdmin, Admin only
    """
    check_scheme_permissions(current_user, "update")
    
    scheme_service = SchemeService(db)
    scheme = scheme_service.update_scheme(scheme_id, scheme_data)
    
    return SchemeOut.model_validate(scheme)


@router.patch("/{scheme_id}/status", response_model=SchemeOut)
async def update_scheme_status(
    scheme_id: int,
    status_data: SchemeStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a scheme.
    
    **Permissions**: SuperAdmin, Admin only
    """
    check_scheme_permissions(current_user, "update")
    
    scheme_service = SchemeService(db)
    scheme = scheme_service.update_scheme_status(scheme_id, status_data.is_active)
    
    return SchemeOut.model_validate(scheme)


@router.delete("/{scheme_id}", response_model=StandardResponse)
async def delete_scheme(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a scheme (soft delete by deactivating).
    
    **Permissions**: SuperAdmin, Admin only
    """
    check_scheme_permissions(current_user, "delete")
    
    scheme_service = SchemeService(db)
    success = scheme_service.delete_scheme(scheme_id)
    
    if success:
        return StandardResponse(
            success=True,
            message="Scheme deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete scheme"
        )


# ========== OWNERSHIP MANAGEMENT ENDPOINTS ==========

@router.put("/{scheme_id}/transfer-ownership", response_model=SchemeOut)
async def transfer_scheme_ownership(
    scheme_id: int,
    new_owner_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transfer ownership of a scheme to another user.
    
    **Permissions**: SuperAdmin, Admin, or current owner
    """
    scheme_service = SchemeService(db)
    user_role = current_user.role.name.lower()
    
    scheme = scheme_service.transfer_scheme_ownership(
        scheme_id, new_owner_id, current_user.id, user_role
    )
    
    return SchemeOut.model_validate(scheme)


@router.put("/{scheme_id}/share-with-user", response_model=SchemeOut)
async def share_scheme_with_user(
    scheme_id: int,
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share scheme with specific user.
    
    **Permissions**: Scheme owner or higher role
    """
    scheme_service = SchemeService(db)
    user_role = current_user.role.name.lower()
    
    scheme = scheme_service.share_scheme_with_user(
        scheme_id, target_user_id, current_user.id, user_role
    )
    
    return SchemeOut.model_validate(scheme)


@router.delete("/{scheme_id}/remove-user-access", response_model=SchemeOut)
async def remove_scheme_user_access(
    scheme_id: int,
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove user access from shared scheme.
    
    **Permissions**: Scheme owner or higher role
    """
    scheme_service = SchemeService(db)
    user_role = current_user.role.name.lower()
    
    scheme = scheme_service.remove_scheme_user_access(
        scheme_id, target_user_id, current_user.id, user_role
    )
    
    return SchemeOut.model_validate(scheme)