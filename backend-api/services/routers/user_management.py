"""
User Management APIs for profile, member management, and user operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from database.database import get_db
from services.auth.auth import get_current_user
from services.models.models import User, Role
from services.models.user_models import UserProfile, KYCDocument, MPIN
from services.schemas.user_schemas import (
    UserProfileCreate, UserProfileUpdate, UserProfileOut,
    UserCreateEnhanced, UserOutEnhanced, MemberCreateRequest, MemberListResponse
)
from config.constants import ROLE_HIERARCHY, ROLE_PREFIX_MAP
import secrets
import string

router = APIRouter(prefix="/users", tags=["User Management"])

def generate_user_code(role: str, db: Session) -> str:
    """Generate unique user code based on role using centralized utility"""
    from utils.user_code_generator import generate_unique_user_code
    return generate_unique_user_code(role, db)

# Profile Management
@router.get("/profile", response_model=UserProfileOut)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    profile = db.query(UserProfile).filter(
        UserProfile.user_code == current_user.user_code
    ).first()
    
    if not profile:
        # Create default profile if not exists
        profile = UserProfile(
            user_id=current_user.id,
            user_code=current_user.user_code
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile

@router.put("/profile", response_model=UserProfileOut)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    profile = db.query(UserProfile).filter(
        UserProfile.user_code == current_user.user_code
    ).first()
    
    if not profile:
        # Create new profile
        profile = UserProfile(
            user_id=current_user.id,
            user_code=current_user.user_code,
            **profile_data.dict(exclude_unset=True)
        )
        db.add(profile)
    else:
        # Update existing profile
        for key, value in profile_data.dict(exclude_unset=True).items():
            setattr(profile, key, value)
        profile.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/profile/{user_code}", response_model=UserProfileOut)
async def get_user_profile_by_code(
    user_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile by user_code (for higher role users)"""
    # Check if current user has permission to view this profile
    target_user = db.query(User).filter(User.user_code == user_code).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Role hierarchy check
    current_role_level = ROLE_HIERARCHY.get(current_user.role.name, 999)
    target_role_level = ROLE_HIERARCHY.get(target_user.role.name, 999)
    
    if current_role_level > target_role_level:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    profile = db.query(UserProfile).filter(
        UserProfile.user_code == user_code
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile

# Member Management
@router.get("/members", response_model=MemberListResponse)
async def get_members(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role_filter: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of sub-members for current user"""
    current_role_level = ROLE_HIERARCHY.get(current_user.role.name, 999)
    
    # Build query for users with lower role levels
    query = db.query(User).join(Role).filter(
        Role.name.in_([
            role for role, level in ROLE_HIERARCHY.items() 
            if level > current_role_level
        ])
    )
    
    # Apply filters
    if role_filter:
        query = query.filter(Role.name == role_filter)
    
    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.user_code.ilike(f"%{search}%"))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    members = query.offset(offset).limit(limit).all()
    
    # Prepare response with additional info
    enhanced_members = []
    for member in members:
        # Get KYC status
        kyc = db.query(KYCDocument).filter(
            KYCDocument.user_code == member.user_code
        ).first()
        kyc_status = kyc.status if kyc else "not_submitted"
        
        # Get MPIN status
        mpin = db.query(MPIN).filter(
            MPIN.user_code == member.user_code
        ).first()
        mpin_set = mpin.is_set if mpin else False
        
        # Get profile status
        profile = db.query(UserProfile).filter(
            UserProfile.user_code == member.user_code
        ).first()
        profile_complete = bool(profile and profile.business_name)
        
        enhanced_member = UserOutEnhanced(
            id=member.id,
            user_code=member.user_code,
            full_name=member.full_name,
            email=member.email,
            phone=member.phone,
            role=member.role.name,
            is_active=member.is_active,
            created_at=member.created_at,
            kyc_status=kyc_status,
            mpin_set=mpin_set,
            profile_complete=profile_complete
        )
        enhanced_members.append(enhanced_member)
    
    return MemberListResponse(
        members=enhanced_members,
        total=total,
        page=page,
        limit=limit
    )

@router.post("/members", response_model=UserOutEnhanced)
async def create_member(
    member_data: MemberCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sub-member"""
    current_role_level = ROLE_HIERARCHY.get(current_user.role.name, 999)
    target_role_level = ROLE_HIERARCHY.get(member_data.role, 999)
    
    # Check if current user can create this role
    if current_role_level >= target_role_level:
        raise HTTPException(
            status_code=403, 
            detail="Cannot create member with same or higher role level"
        )
    
    # Check if email/phone already exists
    existing_user = db.query(User).filter(
        (User.email == member_data.email) | (User.phone == member_data.phone)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or phone already exists"
        )
    
    # Get role
    role = db.query(Role).filter(Role.name == member_data.role).first()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Generate user code and temporary password
    user_code = generate_user_code(member_data.role, db)
    temp_password = f"{user_code.lower()}@123"  # Temporary password
    
    # Create user
    from services.auth.auth import get_password_hash
    new_user = User(
        user_code=user_code,
        username=member_data.email,  # Use email as username
        email=member_data.email,
        phone=member_data.phone,
        full_name=member_data.full_name,
        hashed_password=get_password_hash(temp_password),
        role_id=role.id,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create profile if business_name provided
    if member_data.business_name:
        profile = UserProfile(
            user_id=new_user.id,
            user_code=new_user.user_code,
            business_name=member_data.business_name
        )
        db.add(profile)
        db.commit()
    
    # TODO: Send welcome email with credentials
    
    return UserOutEnhanced(
        id=new_user.id,
        user_code=new_user.user_code,
        full_name=new_user.full_name,
        email=new_user.email,
        phone=new_user.phone,
        role=new_user.role.name,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        kyc_status="not_submitted",
        mpin_set=False,
        profile_complete=bool(member_data.business_name)
    )

@router.get("/members/{user_code}", response_model=UserOutEnhanced)
async def get_member_details(
    user_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific member"""
    # Get member
    member = db.query(User).filter(User.user_code == user_code).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Role hierarchy check
    current_role_level = ROLE_HIERARCHY.get(current_user.role.name, 999)
    member_role_level = ROLE_HIERARCHY.get(member.role.name, 999)
    
    if current_role_level >= member_role_level:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get additional info
    kyc = db.query(KYCDocument).filter(
        KYCDocument.user_code == user_code
    ).first()
    kyc_status = kyc.status if kyc else "not_submitted"
    
    mpin = db.query(MPIN).filter(
        MPIN.user_code == user_code
    ).first()
    mpin_set = mpin.is_set if mpin else False
    
    profile = db.query(UserProfile).filter(
        UserProfile.user_code == user_code
    ).first()
    profile_complete = bool(profile and profile.business_name)
    
    return UserOutEnhanced(
        id=member.id,
        user_code=member.user_code,
        full_name=member.full_name,
        email=member.email,
        phone=member.phone,
        role=member.role.name,
        is_active=member.is_active,
        created_at=member.created_at,
        kyc_status=kyc_status,
        mpin_set=mpin_set,
        profile_complete=profile_complete
    )

@router.put("/members/{user_code}/status")
async def update_member_status(
    user_code: str,
    is_active: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate/Deactivate a member"""
    # Get member
    member = db.query(User).filter(User.user_code == user_code).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Role hierarchy check
    current_role_level = ROLE_HIERARCHY.get(current_user.role.name, 999)
    member_role_level = ROLE_HIERARCHY.get(member.role.name, 999)
    
    if current_role_level >= member_role_level:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    member.is_active = is_active
    member.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Member {'activated' if is_active else 'deactivated'} successfully",
        "user_code": user_code,
        "is_active": is_active
    }

# User Statistics
@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics for dashboard"""
    current_role_level = ROLE_HIERARCHY.get(current_user.role.name, 999)
    
    # Get subordinate roles
    subordinate_roles = [
        role for role, level in ROLE_HIERARCHY.items() 
        if level > current_role_level
    ]
    
    # Count members by role
    stats = {}
    for role in subordinate_roles:
        count = db.query(User).join(Role).filter(Role.name == role).count()
        stats[f"{role}_count"] = count
    
    # Count KYC statuses
    pending_kyc = db.query(KYCDocument).filter(
        KYCDocument.status == "pending"
    ).count()
    approved_kyc = db.query(KYCDocument).filter(
        KYCDocument.status == "approved"
    ).count()
    
    stats.update({
        "total_members": sum(stats.values()),
        "pending_kyc": pending_kyc,
        "approved_kyc": approved_kyc
    })
    
    return stats