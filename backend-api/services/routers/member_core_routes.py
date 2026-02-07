"""
Member Management API Routes
Clean, modular API layer using service layer for business logic
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from database.database import get_db
from services.models.models import User
from services.schemas.member_schema import (
    MemberCreateRequest, MemberCreateResponse,
    MemberOut, MemberListResponse,
    MemberUpdateRequest, MemberUpdateResponse,
    MemberStatusUpdateRequest, MemberDeleteResponse
)
from services.auth.auth import get_current_user
from services.business.member_service import member_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/members", tags=["Member Management"])

# ======================== Member CRUD Operations ========================

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

@router.get("/list", response_model=MemberListResponse)
def list_members(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List members that current user can manage"""
    logger.info(f"Listing members requested by user '{current_user.user_code}' - page: {page}, limit: {limit}, role: {role}")
    
    member_list, total = member_service.list_members(
        current_user, db, page, limit, role, is_active, search
    )
    
    logger.info(f"Retrieved {len(member_list)} members out of {total} total for user '{current_user.user_code}'")
    
    return MemberListResponse(
        members=member_list,
        total=total,
        page=page,
        limit=limit
    )

@router.get("/{member_id}", response_model=MemberOut)
def get_member_details(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific member"""
    return member_service.get_member_details(member_id, current_user, db)

@router.put("/{member_id}", response_model=MemberUpdateResponse)
def update_member(
    member_id: int,
    update_data: MemberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update member information"""
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