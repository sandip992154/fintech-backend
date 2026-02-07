"""
Role-based Member Management API
Provides endpoints for adding, updating, and deleting users based on role hierarchy
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import secrets
import string

from database.database import get_db
from services.models.models import User, Role
from services.schemas.member_schema import (
    MemberCreateRequest, MemberCreateResponse,
    MemberOut, MemberListResponse,
    MemberUpdateRequest, MemberUpdateResponse,
    MemberStatusUpdateRequest,
    MemberDeleteResponse,
    MemberStatsResponse,
    UserRolePermissionsResponse, RoleHierarchyResponse,
    ParentSelectionOption, ParentSelectionResponse,
    RoleBasedMemberListRequest, EnhancedMemberListResponse
)
from services.schemas.member_admin_schema import (
    MemberAdminListOut, MemberAdminListResponse, MemberListRequest,
    MemberExportRequest, SchemeListResponse, SchemeOption,
    LocationOptionsResponse, StateOption, CityOption,
    MemberDashboardStats, BulkMemberAction, BulkActionResponse
)
from services.auth.auth import get_current_user, get_password_hash
from config.constants import ROLE_HIERARCHY, ROLE_PREFIX_MAP
from utils.email_utils import send_account_email
from config.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api/v1/members", tags=["Member Management"])
logger = logging.getLogger(__name__)

# ======================== Helper Functions ========================

def get_role_level(role_name: str) -> int:
    """Get the hierarchy level of a role"""
    return ROLE_HIERARCHY.get(role_name, {}).get("level", 999)

def can_manage_role(current_role: str, target_role: str) -> bool:
    """Check if current user can manage target role"""
    current_level = get_role_level(current_role)
    target_level = get_role_level(target_role)
    return current_level < target_level

def get_creatable_roles(current_role: str) -> List[str]:
    """Get list of roles that current user can create"""
    return ROLE_HIERARCHY.get(current_role, {}).get("can_create", [])

def get_manageable_roles(current_role: str) -> List[str]:
    """Get list of roles that current user can manage"""
    current_level = get_role_level(current_role)
    manageable = []
    for role, config in ROLE_HIERARCHY.items():
        if config["level"] > current_level:
            manageable.append(role)
    return manageable

def validate_member_permissions(current_user: User, target_role: str, action: str = "create"):
    """Validate if current user has permission to perform action on target role"""
    current_role = current_user.role.name
    
    if action == "create":
        creatable_roles = get_creatable_roles(current_role)
        if target_role not in creatable_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission to create {target_role} members. You can only create: {', '.join(creatable_roles)}"
            )
    elif action in ["update", "delete", "manage"]:
        if not can_manage_role(current_role, target_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission to {action} {target_role} members"
            )

def generate_user_code(role: str, db: Session) -> str:
    """Generate unique user code for the role using centralized utility"""
    from utils.user_code_generator import generate_unique_user_code
    return generate_unique_user_code(role, db)

def generate_secure_password(length: int = 12) -> str:
    """Generate a secure random password"""
    # Ensure password has at least one character from each category
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*"
    
    # Ensure at least one character from each category
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill the rest randomly
    all_chars = lowercase + uppercase + digits + special_chars
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password list
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

# ======================== Role Hierarchy and Permissions ========================

@router.get("/role-permissions", response_model=UserRolePermissionsResponse)
def get_user_role_permissions(
    current_user: User = Depends(get_current_user)
):
    """Get current user's role permissions and hierarchy information"""
    current_role = current_user.role.name
    current_level = get_role_level(current_role)
    
    hierarchy = []
    for role, config in ROLE_HIERARCHY.items():
        hierarchy.append(RoleHierarchyResponse(
            role=role,
            level=config["level"],
            description=config["description"],
            can_create=config["can_create"],
            manageable_roles=get_manageable_roles(role)
        ))
    
    # Sort hierarchy by level
    hierarchy.sort(key=lambda x: x.level)
    
    return UserRolePermissionsResponse(
        current_role=current_role,
        level=current_level,
        creatable_roles=get_creatable_roles(current_role),
        manageable_roles=get_manageable_roles(current_role),
        hierarchy=hierarchy
    )

# ======================== Member Creation ========================

@router.post("/create", response_model=MemberCreateResponse)
def create_member(
    member_data: MemberCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new member with role-based permissions"""
    try:
        # Validate permissions
        validate_member_permissions(current_user, member_data.role_name, "create")
        
        # Check if email or phone already exists
        existing_user = db.query(User).filter(
            (User.email == member_data.email) | (User.phone == member_data.phone)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or phone already exists"
            )
        
        # Get role object
        role_obj = db.query(Role).filter(Role.name == member_data.role_name).first()
        if not role_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{member_data.role_name}' not found"
            )
        
        # Generate user code
        user_code = generate_user_code(member_data.role_name, db)
        
        # Use user_code as default password if not provided
        raw_password = member_data.password if member_data.password else user_code
        
        # Auto-assign parent for specific roles
        parent_id = member_data.parent_id
        if member_data.role_name == "Admin" and not parent_id:
            # Auto-assign SuperAdmin as parent for Admin
            superadmin = db.query(User).join(Role).filter(Role.name == "SuperAdmin").first()
            if superadmin:
                parent_id = superadmin.id
        
        # Validate parent exists and is valid for the role hierarchy
        if parent_id:
            parent_user = db.query(User).filter(User.id == parent_id).first()
            if not parent_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent user not found"
                )
            
            # Validate parent role hierarchy
            parent_role = parent_user.role.name
            if not can_manage_role(parent_role, member_data.role_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{parent_role} cannot be parent of {member_data.role_name}"
                )
        
        # Create new user
        new_member = User(
            user_code=user_code,
            username=user_code,  # Set username to user_code for consistent login
            email=member_data.email,
            phone=member_data.phone,
            mobile=member_data.mobile,
            full_name=member_data.full_name,
            hashed_password=get_password_hash(raw_password),
            role_id=role_obj.id,
            parent_id=parent_id,
            
            # Address fields (Updated)
            address=member_data.address,
            pin_code=member_data.pin_code,
            
            # Business fields (Updated)
            shop_name=member_data.shop_name,
            company_name=getattr(member_data, 'company_name', None),
            scheme=member_data.scheme,
            
            # KYC fields (Updated)
            pan_card_number=member_data.pan_card_number,
            company_pan_card=member_data.company_pan_card,
            aadhaar_card_number=member_data.aadhaar_card_number,
            
            # Business fields
            shop_name=member_data.shop_name,
            scheme=member_data.scheme,
            
            # KYC fields
            pan_card_number=member_data.pan_card_number,
            aadhaar_card_number=member_data.aadhaar_card_number,
            
            # Member management fields
            company_pan_card=member_data.company_pan_card,
            parent_id=current_user.id,  # Set current user as parent in hierarchy
            
            is_active=True
        )
        
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        
        # Send welcome email with login credentials
        email_error = None
        try:
            # Create login link (you can customize this based on your frontend URL)
            login_link = f"{getattr(settings, 'FRONTEND_URL', 'https://app.bandarupay.com')}/login"
            
            email_error = send_account_email(
                smtp_server=settings.SMTP_SERVER,
                smtp_port=settings.SMTP_PORT,
                smtp_user=settings.SMTP_USER,
                smtp_password=settings.SMTP_PASSWORD,
                to_email=new_member.email,
                user_id=new_member.user_code,
                password=raw_password,
                signup_link=login_link,
                role=new_member.role.name
            )
            
            if email_error:
                logger.warning(f"Failed to send welcome email to {new_member.email}: {email_error}")
            else:
                logger.info(f"Welcome email sent successfully to {new_member.email}")
                
        except Exception as email_exception:
            logger.error(f"Email sending failed: {str(email_exception)}")
            email_error = str(email_exception)
            # Don't fail the entire operation if email fails
        
        # Load the role for response
        db.refresh(new_member)
        
        # Create response
        member_out = MemberOut(
            id=new_member.id,
            user_code=new_member.user_code,
            full_name=new_member.full_name,
            email=new_member.email,
            phone=new_member.phone,
            mobile=new_member.mobile,
            address=new_member.address,
            city=new_member.city,
            state=new_member.state,
            pin_code=new_member.pin_code,
            shop_name=new_member.shop_name,
            scheme=new_member.scheme,
            pan_card_number=new_member.pan_card_number,
            aadhaar_card_number=new_member.aadhaar_card_number,
            role=new_member.role.name,
            role_id=new_member.role_id,
            role_name=new_member.role.name,
            is_active=new_member.is_active,
            created_at=new_member.created_at,
            updated_at=new_member.updated_at,
            profile_complete=bool(new_member.pan_card_number and new_member.aadhaar_card_number)
        )
        
        logger.info(f"Member created successfully: {new_member.user_code} by {current_user.user_code}")
        
        # Create success message
        success_message = f"{member_data.role.title()} member created successfully. "
        if not email_error:
            success_message += "Login credentials sent to email."
        else:
            success_message += "Please share login credentials manually (email failed)."
        
        return MemberCreateResponse(
            member=member_out,
            message=success_message
        )
        
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        elif "phone" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Member creation failed due to data conflict"
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create member"
        )

# ======================== Enhanced Member Listing for Admin Panel ========================

@router.post("/admin/list", response_model=MemberAdminListResponse)
def list_members_admin(
    request: MemberListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enhanced member listing for admin panel with advanced filters"""
    try:
        # Get manageable roles
        manageable_roles = get_manageable_roles(current_user.role.name)
        
        if not manageable_roles:
            return MemberAdminListResponse(
                members=[], total=0, page=request.page, limit=request.limit,
                total_pages=0, has_next=False, has_prev=False
            )
        
        # Build base query with joins
        query = db.query(User).options(
            joinedload(User.role),
            joinedload(User.parent)
        ).filter(
            User.role.has(Role.name.in_(manageable_roles))
        )
        
        # Apply date filters
        if request.from_date:
            query = query.filter(User.created_at >= request.from_date)
        if request.to_date:
            query = query.filter(User.created_at <= request.to_date)
        
        # Apply role filter
        if request.role and request.role in manageable_roles:
            query = query.filter(User.role.has(Role.name == request.role))
        
        # Apply status filter
        if request.is_active is not None:
            query = query.filter(User.is_active == request.is_active)
        
        # Apply search filter
        if request.search_value:
            search_term = f"%{request.search_value}%"
            query = query.filter(
                (User.full_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.phone.ilike(search_term)) |
                (User.user_code.ilike(search_term))
            )
        
        # Apply parent/agent filter
        if request.agent_parent:
            query = query.filter(User.parent.has(User.user_code == request.agent_parent))
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        total_pages = (total + request.limit - 1) // request.limit
        has_next = request.page < total_pages
        has_prev = request.page > 1
        
        # Apply pagination and ordering
        offset = (request.page - 1) * request.limit
        members = query.order_by(desc(User.created_at)).offset(offset).limit(request.limit).all()
        
        # Convert to enhanced response format
        member_list = []
        total_wallet_balance = 0.0
        active_count = 0
        inactive_count = 0
        
        for member in members:
            # Parent details
            parent_details = None
            if member.parent:
                parent_details = {
                    "user_code": member.parent.user_code,
                    "full_name": member.parent.full_name,
                    "phone": member.parent.phone,
                    "role": member.parent.role.name
                }
            
            # Company profile
            company_profile = {
                "company_pan": member.company_pan_card,
                "shop_name": member.shop_name,
                "scheme": member.scheme,
                "registration_date": member.created_at.strftime("%d/%m/%Y") if member.created_at else None
            }
            
            # Wallet details (placeholder - integrate with actual wallet system)
            wallet_details = {
                "main_balance": 0.0,
                "aeps_balance": 0.0,
                "commission_balance": 0.2,  # Example
                "total_balance": 0.2
            }
            total_wallet_balance += wallet_details["total_balance"]
            
            # ID Stock (for distributor/retailer hierarchy)
            id_stock = {
                "admin_count": 1 if member.role.name == "admin" else 0,
                "md_count": 1 if member.role.name == "mds" else 0,
                "distributor_count": 1 if member.role.name == "distributor" else 0,
                "retailer_count": 1 if member.role.name == "retailer" else 0
            }
            
            # Status tracking
            if member.is_active:
                active_count += 1
            else:
                inactive_count += 1
            
            member_admin = MemberAdminListOut(
                id=member.id,
                user_code=member.user_code,
                full_name=member.full_name,
                email=member.email,
                phone=member.phone,
                mobile=member.mobile,
                role=member.role.name,
                role_name=member.role.name,
                is_active=member.is_active,
                created_at=member.created_at,
                updated_at=member.updated_at,
                parent_details=parent_details,
                company_profile=company_profile,
                wallet_details=wallet_details,
                id_stock=id_stock,
                status="active" if member.is_active else "inactive"
            )
            member_list.append(member_admin)
        
        # Summary stats
        summary = {
            "total_active": active_count,
            "total_inactive": inactive_count,
            "total_wallet_balance": total_wallet_balance
        }
        
        return MemberAdminListResponse(
            members=member_list,
            total=total,
            page=request.page,
            limit=request.limit,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin member list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch member list"
        )

# ======================== Member Export ========================

@router.post("/admin/export")
def export_members(
    request: MemberExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export member data in various formats"""
    try:
        # For now, return success message (implement actual export logic as needed)
        return {
            "success": True,
            "message": f"Export initiated for {request.format} format",
            "download_url": f"/downloads/members_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}"
        }
    except Exception as e:
        logger.error(f"Error exporting members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export members"
        )

# ======================== Scheme Management ========================

@router.get("/schemes", response_model=SchemeListResponse)
def get_schemes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available schemes for member creation"""
    try:
        # Placeholder schemes - integrate with actual scheme system
        schemes = [
            SchemeOption(id="premium", name="Premium Plan", description="Premium commission structure", commission_rate=2.5),
            SchemeOption(id="standard", name="Standard Plan", description="Standard commission structure", commission_rate=2.0),
            SchemeOption(id="basic", name="Basic Plan", description="Basic commission structure", commission_rate=1.5)
        ]
        
        return SchemeListResponse(schemes=schemes, total=len(schemes))
        
    except Exception as e:
        logger.error(f"Error fetching schemes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch schemes"
        )

# ======================== Location Data ========================

@router.get("/locations", response_model=LocationOptionsResponse)
def get_locations(
    state_id: Optional[str] = Query(None, description="Get cities for specific state"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get states and cities for form dropdowns"""
    try:
        # Placeholder location data - integrate with actual location system
        states = [
            StateOption(id="MH", name="Maharashtra", code="MH"),
            StateOption(id="DL", name="Delhi", code="DL"),
            StateOption(id="KA", name="Karnataka", code="KA"),
            StateOption(id="TN", name="Tamil Nadu", code="TN"),
            StateOption(id="TG", name="Telangana", code="TG"),
            StateOption(id="UP", name="Uttar Pradesh", code="UP")
        ]
        
        cities = []
        if state_id:
            city_map = {
                "MH": [CityOption(id="mumbai", name="Mumbai", state_id="MH"), CityOption(id="pune", name="Pune", state_id="MH")],
                "DL": [CityOption(id="delhi", name="Delhi", state_id="DL")],
                "KA": [CityOption(id="bangalore", name="Bangalore", state_id="KA")],
                "TN": [CityOption(id="chennai", name="Chennai", state_id="TN")],
                "TG": [CityOption(id="hyderabad", name="Hyderabad", state_id="TG")]
            }
            cities = city_map.get(state_id, [])
        
        return LocationOptionsResponse(states=states, cities=cities)
        
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch location data"
        )

# ======================== Dashboard Stats ========================

@router.get("/admin/dashboard", response_model=MemberDashboardStats)
def get_member_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for member management"""
    try:
        # Get manageable roles
        manageable_roles = get_manageable_roles(current_user.role.name)
        
        # Base query for manageable users
        base_query = db.query(User).filter(
            User.role.has(Role.name.in_(manageable_roles))
        )
        
        # Basic counts
        total_members = base_query.count()
        active_members = base_query.filter(User.is_active == True).count()
        inactive_members = total_members - active_members
        
        # KYC stats (placeholder)
        completed_kyc = base_query.filter(
            User.pan_card_number.isnot(None),
            User.aadhaar_card_number.isnot(None)
        ).count()
        pending_kyc = total_members - completed_kyc
        
        # Role distribution
        role_distribution = {}
        for role in manageable_roles:
            count = base_query.filter(User.role.has(Role.name == role)).count()
            if count > 0:
                role_distribution[role] = count
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_registrations = base_query.filter(User.created_at >= seven_days_ago).count()
        
        # Recent activations (users who became active in last 7 days) - placeholder
        recent_activations = 0
        
        return MemberDashboardStats(
            total_members=total_members,
            active_members=active_members,
            inactive_members=inactive_members,
            pending_kyc=pending_kyc,
            completed_kyc=completed_kyc,
            role_distribution=role_distribution,
            recent_registrations=recent_registrations,
            recent_activations=recent_activations,
            total_wallet_balance=0.0  # Integrate with wallet system
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard statistics"
        )

# ======================== Original Member Listing ========================

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
    try:
        # Get manageable roles
        manageable_roles = get_manageable_roles(current_user.role.name)
        
        if not manageable_roles:
            return MemberListResponse(members=[], total=0, page=page, limit=limit)
        
        # Build query
        query = db.query(User).options(joinedload(User.role)).filter(
            User.role.has(Role.name.in_(manageable_roles))
        )
        
        # Apply filters
        if role:
            if role not in manageable_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You cannot view {role} members"
                )
            query = query.filter(User.role.has(Role.name == role))
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.phone.ilike(search_term)) |
                (User.user_code.ilike(search_term))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        members = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
        
        # Convert to response format
        member_list = []
        for member in members:
            # Normalize phone numbers to handle international format
            def normalize_phone(phone_str):
                if not phone_str:
                    return phone_str
                # Remove +91 prefix if present
                if phone_str.startswith('+91'):
                    return phone_str[3:]
                if phone_str.startswith('91') and len(phone_str) == 12:
                    return phone_str[2:]
                return phone_str
            
            member_out = MemberOut(
                id=member.id,
                user_code=member.user_code,
                full_name=member.full_name,
                email=member.email,
                phone=normalize_phone(member.phone),
                mobile=normalize_phone(member.mobile),
                address=member.address,
                city=member.city,
                state=member.state,
                pin_code=member.pin_code,
                shop_name=member.shop_name,
                scheme=member.scheme,
                pan_card_number=member.pan_card_number,
                aadhaar_card_number=member.aadhaar_card_number,
                role=member.role.name,
                role_id=member.role_id,
                role_name=member.role.name,
                is_active=member.is_active,
                created_at=member.created_at,
                updated_at=member.updated_at,
                profile_complete=bool(member.pan_card_number and member.aadhaar_card_number)
            )
            member_list.append(member_out)
        
        return MemberListResponse(
            members=member_list,
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve members"
        )

# ======================== Member Details ========================

@router.get("/{member_id}", response_model=MemberOut)
def get_member_details(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific member"""
    try:
        # Get member
        member = db.query(User).options(joinedload(User.role)).filter(User.id == member_id).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Check permissions
        validate_member_permissions(current_user, member.role.name, "manage")
        
        member_out = MemberOut(
            id=member.id,
            user_code=member.user_code,
            full_name=member.full_name,
            email=member.email,
            phone=member.phone,
            mobile=member.mobile,
            address=member.address,
            city=member.city,
            state=member.state,
            pin_code=member.pin_code,
            shop_name=member.shop_name,
            scheme=member.scheme,
            pan_card_number=member.pan_card_number,
            aadhaar_card_number=member.aadhaar_card_number,
            role=member.role.name,
            role_id=member.role_id,
            role_name=member.role.name,
            is_active=member.is_active,
            created_at=member.created_at,
            updated_at=member.updated_at,
            profile_complete=bool(member.pan_card_number and member.aadhaar_card_number)
        )
        
        return member_out
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting member details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve member details"
        )

# ======================== Member Update ========================

@router.put("/{member_id}", response_model=MemberUpdateResponse)
def update_member(
    member_id: int,
    update_data: MemberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update member information"""
    try:
        # Get member
        member = db.query(User).options(joinedload(User.role)).filter(User.id == member_id).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Check permissions
        validate_member_permissions(current_user, member.role.name, "update")
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if hasattr(member, field):
                setattr(member, field, value)
        
        member.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(member)
        
        member_out = MemberOut(
            id=member.id,
            user_code=member.user_code,
            full_name=member.full_name,
            email=member.email,
            phone=member.phone,
            mobile=member.mobile,
            address=member.address,
            city=member.city,
            state=member.state,
            pin_code=member.pin_code,
            shop_name=member.shop_name,
            scheme=member.scheme,
            pan_card_number=member.pan_card_number,
            aadhaar_card_number=member.aadhaar_card_number,
            role=member.role.name,
            role_id=member.role_id,
            role_name=member.role.name,
            is_active=member.is_active,
            created_at=member.created_at,
            updated_at=member.updated_at,
            profile_complete=bool(member.pan_card_number and member.aadhaar_card_number)
        )
        
        logger.info(f"Member updated: {member.user_code} by {current_user.user_code}")
        
        return MemberUpdateResponse(
            member=member_out,
            message="Member updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update member"
        )

# ======================== Member Status Update ========================

@router.patch("/{member_id}/status", response_model=dict)
def update_member_status(
    member_id: int,
    status_data: MemberStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update member active status"""
    try:
        # Get member
        member = db.query(User).options(joinedload(User.role)).filter(User.id == member_id).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Check permissions
        validate_member_permissions(current_user, member.role.name, "update")
        
        # Update status
        member.is_active = status_data.is_active
        member.updated_at = datetime.utcnow()
        
        db.commit()
        
        action = "activated" if status_data.is_active else "deactivated"
        logger.info(f"Member {action}: {member.user_code} by {current_user.user_code}")
        
        return {
            "message": f"Member {action} successfully",
            "success": True,
            "member_id": member_id,
            "is_active": status_data.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating member status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update member status"
        )

# ======================== Member Deletion ========================

@router.delete("/{member_id}", response_model=MemberDeleteResponse)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a member (soft delete by deactivating)"""
    try:
        # Get member
        member = db.query(User).options(joinedload(User.role)).filter(User.id == member_id).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Check permissions
        validate_member_permissions(current_user, member.role.name, "delete")
        
        # Soft delete (deactivate)
        member.is_active = False
        member.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Member deleted: {member.user_code} by {current_user.user_code}")
        
        return MemberDeleteResponse(
            message="Member deleted successfully",
            member_id=member_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete member"
        )

# ======================== Member Statistics ========================

@router.get("/stats/overview", response_model=MemberStatsResponse)
def get_member_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get member statistics for current user's manageable roles"""
    try:
        # Get manageable roles
        manageable_roles = get_manageable_roles(current_user.role.name)
        
        if not manageable_roles:
            return MemberStatsResponse(
                total_members=0,
                active_members=0,
                inactive_members=0,
                role_distribution={},
                recent_additions=0
            )
        
        # Base query for manageable members
        base_query = db.query(User).filter(
            User.role.has(Role.name.in_(manageable_roles))
        )
        
        # Total members
        total_members = base_query.count()
        
        # Active/Inactive members
        active_members = base_query.filter(User.is_active == True).count()
        inactive_members = total_members - active_members
        
        # Role distribution
        role_stats = db.query(
            Role.name,
            func.count(User.id).label('count')
        ).join(User).filter(
            Role.name.in_(manageable_roles)
        ).group_by(Role.name).all()
        
        role_distribution = {role: count for role, count in role_stats}
        
        # Recent additions (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_additions = base_query.filter(
            User.created_at >= week_ago
        ).count()
        
        return MemberStatsResponse(
            total_members=total_members,
            active_members=active_members,
            inactive_members=inactive_members,
            role_distribution=role_distribution,
            recent_additions=recent_additions
        )
        
    except Exception as e:
        logger.error(f"Error getting member statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve member statistics"
        )

# ======================== Additional Admin Panel APIs ========================

@router.get("/admin/parents")
def get_parent_options(
    role: Optional[str] = Query(None, description="Filter parents by role"),
    search: Optional[str] = Query(None, description="Search parents"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of potential parents/agents for dropdown"""
    try:
        # Get roles that can be parents (one level up from target role)
        manageable_roles = get_manageable_roles(current_user.role.name)
        
        # Build query for potential parents
        query = db.query(User).filter(
            User.role.has(Role.name.in_(manageable_roles)),
            User.is_active == True
        )
        
        if role:
            # If creating a specific role, filter to appropriate parent roles
            parent_roles = []
            current_level = get_role_level(current_user.role.name)
            target_level = get_role_level(role)
            
            # Get all roles between current user and target role
            for role_name, config in ROLE_HIERARCHY.items():
                if current_level <= config["level"] < target_level:
                    parent_roles.append(role_name)
            
            if parent_roles:
                query = query.filter(User.role.has(Role.name.in_(parent_roles)))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(search_term)) |
                (User.user_code.ilike(search_term))
            )
        
        parents = query.order_by(User.full_name).limit(50).all()
        
        parent_options = []
        for parent in parents:
            parent_options.append({
                "id": parent.id,
                "user_code": parent.user_code,
                "full_name": parent.full_name,
                "role": parent.role.name,
                "phone": parent.phone
            })
        
        return {
            "success": True,
            "parents": parent_options,
            "total": len(parent_options)
        }
        
    except Exception as e:
        logger.error(f"Error fetching parent options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch parent options"
        )

@router.post("/admin/bulk-action", response_model=BulkActionResponse)
def bulk_member_action(
    request: BulkMemberAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk actions on members"""
    try:
        # Get manageable roles
        manageable_roles = get_manageable_roles(current_user.role.name)
        
        # Get members to act upon
        members = db.query(User).filter(
            User.id.in_(request.member_ids),
            User.role.has(Role.name.in_(manageable_roles))
        ).all()
        
        if len(members) != len(request.member_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action on some selected members"
            )
        
        processed_count = 0
        failed_count = 0
        failed_items = []
        
        for member in members:
            try:
                if request.action == "activate":
                    member.is_active = True
                elif request.action == "deactivate":
                    member.is_active = False
                elif request.action == "delete":
                    # Soft delete - set inactive and add deletion reason
                    member.is_active = False
                    # In a real implementation, you might have a deletion table
                elif request.action == "export":
                    # For export, just count as processed
                    pass
                
                processed_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_items.append({
                    "member_id": member.id,
                    "user_code": member.user_code,
                    "error": str(e)
                })
        
        if request.action != "export":
            db.commit()
        
        action_messages = {
            "activate": f"Successfully activated {processed_count} members",
            "deactivate": f"Successfully deactivated {processed_count} members", 
            "delete": f"Successfully deleted {processed_count} members",
            "export": f"Export initiated for {processed_count} members"
        }
        
        return BulkActionResponse(
            success=failed_count == 0,
            message=action_messages.get(request.action, f"Processed {processed_count} members"),
            processed_count=processed_count,
            failed_count=failed_count,
            failed_items=failed_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk action"
        )

@router.get("/admin/member-search")
def search_members_autocomplete(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Autocomplete search for members"""
    try:
        manageable_roles = get_manageable_roles(current_user.role.name)
        
        if not manageable_roles:
            return {"results": []}
        
        query = db.query(User).join(Role).filter(
            Role.name.in_(manageable_roles),
            User.is_active == True,
            (User.full_name.ilike(f"%{q}%") | 
             User.email.ilike(f"%{q}%") | 
             User.phone.ilike(f"%{q}%"))
        ).limit(limit)
        
        members = query.all()
        
        results = []
        for member in members:
            results.append({
                "id": member.id,
                "name": member.full_name,
                "email": member.email,
                "phone": member.phone,
                "role": member.role.name,
                "user_code": member.user_code
            })
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error in member search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search members"
        )

# ===== NEW ENHANCED ENDPOINTS =====

@router.get("/parents/{role_name}", response_model=ParentSelectionResponse)
def get_available_parents(
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available parent options for a specific role"""
    try:
        # Validate role exists
        if role_name not in ROLE_HIERARCHY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role_name}"
            )
        
        # Determine which roles can be parents for this role
        parent_roles = []
        current_role_level = ROLE_HIERARCHY[role_name]["level"]
        
        for parent_role, config in ROLE_HIERARCHY.items():
            if config["level"] < current_role_level:
                # Check if current user can see this parent role
                if can_manage_role(current_user.role.name, parent_role) or current_user.role.name == parent_role:
                    parent_roles.append(parent_role)
        
        if not parent_roles:
            return ParentSelectionResponse(
                success=True,
                parents=[],
                message="No available parents for this role"
            )
        
        # Get available parents
        parents_query = db.query(User).join(Role).filter(
            Role.name.in_(parent_roles),
            User.is_active == True
        ).order_by(Role.name, User.full_name)
        
        # For non-SuperAdmin users, filter by their hierarchy
        if current_user.role.name != "SuperAdmin":
            # Only show parents within their hierarchy
            hierarchy_ids = get_user_hierarchy_ids(current_user.id, db)
            parents_query = parents_query.filter(User.id.in_(hierarchy_ids))
        
        parents = parents_query.all()
        
        parent_options = []
        for parent in parents:
            parent_options.append(ParentSelectionOption(
                id=parent.id,
                name=parent.full_name,
                user_code=parent.user_code,
                role_name=parent.role.name,
                email=parent.email,
                is_active=parent.is_active
            ))
        
        return ParentSelectionResponse(
            success=True,
            parents=parent_options,
            message=f"Found {len(parent_options)} available parents"
        )
        
    except Exception as e:
        logger.error(f"Error getting available parents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available parents"
        )

@router.post("/list/role-based", response_model=EnhancedMemberListResponse)
def get_role_based_member_list(
    request: RoleBasedMemberListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enhanced role-based member listing with filters"""
    try:
        # Validate requesting user
        if current_user.id != request.requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid requesting user"
            )
        
        if current_user.role.name != request.requesting_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role mismatch"
            )
        
        # Build base query
        base_query = db.query(User).join(Role).filter(User.is_active == True)
        
        # Apply role-based filtering
        requesting_role = current_user.role.name
        
        if requesting_role == "SuperAdmin":
            # SuperAdmin sees everyone
            pass
        elif requesting_role == "Admin":
            # Admin sees WhiteLabel, Distributor, Retailer, CustomerSupport
            manageable_roles = ["WhiteLabel", "Distributor", "Retailer", "CustomerSupport"]
            base_query = base_query.filter(Role.name.in_(manageable_roles))
        elif requesting_role == "WhiteLabel":
            # WhiteLabel sees only their hierarchy
            hierarchy_ids = get_user_hierarchy_ids(current_user.id, db)
            base_query = base_query.filter(User.id.in_(hierarchy_ids))
            base_query = base_query.filter(Role.name.in_(["Distributor", "Retailer"]))
        elif requesting_role == "Distributor":
            # Distributor sees only their retailers
            hierarchy_ids = get_user_hierarchy_ids(current_user.id, db)
            base_query = base_query.filter(User.id.in_(hierarchy_ids))
            base_query = base_query.filter(Role.name == "Retailer")
        else:
            # Other roles see no one
            base_query = base_query.filter(User.id == -1)  # No results
        
        # Apply additional filters
        if request.role_filter:
            base_query = base_query.filter(Role.name == request.role_filter)
        
        if request.search_query:
            search_term = f"%{request.search_query}%"
            base_query = base_query.filter(
                (User.full_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.phone.ilike(search_term)) |
                (User.user_code.ilike(search_term))
            )
        
        if request.status_filter == "active":
            base_query = base_query.filter(User.is_active == True)
        elif request.status_filter == "inactive":
            base_query = base_query.filter(User.is_active == False)
        
        if request.parent_filter:
            base_query = base_query.filter(User.parent_id == request.parent_filter)
        
        if request.scheme_filter:
            base_query = base_query.filter(User.scheme == request.scheme_filter)
        
        # Get total count
        total = base_query.count()
        
        # Apply sorting
        if request.sort_by == "name":
            sort_field = User.full_name
        elif request.sort_by == "email":
            sort_field = User.email
        elif request.sort_by == "role":
            sort_field = Role.name
        elif request.sort_by == "created_at":
            sort_field = User.created_at
        else:
            sort_field = User.created_at
        
        if request.sort_order == "asc":
            base_query = base_query.order_by(sort_field.asc())
        else:
            base_query = base_query.order_by(sort_field.desc())
        
        # Apply pagination
        offset = (request.page - 1) * request.limit
        members = base_query.offset(offset).limit(request.limit).all()
        
        # Format members with enhanced data
        member_outputs = []
        for member in members:
            # Get parent name
            parent_name = None
            if member.parent_id:
                parent = db.query(User).filter(User.id == member.parent_id).first()
                if parent:
                    parent_name = parent.full_name
            
            # Get children count
            children_count = db.query(User).filter(User.parent_id == member.id).count()
            
            # Normalize phone numbers for validation
            def normalize_phone(phone_str):
                if not phone_str:
                    return phone_str
                if phone_str.startswith('+91'):
                    return phone_str[3:]
                if phone_str.startswith('91') and len(phone_str) == 12:
                    return phone_str[2:]
                return phone_str
            
            member_out = MemberOut(
                id=member.id,
                user_code=member.user_code,
                full_name=member.full_name,
                email=member.email,
                phone=normalize_phone(member.phone),
                mobile=normalize_phone(member.mobile),
                address=member.address,
                pin_code=member.pin_code,
                shop_name=member.shop_name,
                company_name=getattr(member, 'company_name', None),
                scheme=member.scheme,
                pan_card_number=member.pan_card_number,
                company_pan_card=member.company_pan_card,
                aadhaar_card_number=member.aadhaar_card_number,
                role_id=member.role_id,
                role_name=member.role.name,
                parent_id=member.parent_id,
                parent_name=parent_name,
                is_active=member.is_active,
                created_at=member.created_at,
                updated_at=member.updated_at,
                children_count=children_count,
                profile_complete=bool(member.pan_card_number or member.aadhaar_card_number)
            )
            member_outputs.append(member_out)
        
        return EnhancedMemberListResponse(
            success=True,
            members=member_outputs,
            total=total,
            page=request.page,
            limit=request.limit,
            filters_applied={
                "role_filter": request.role_filter,
                "search_query": request.search_query,
                "status_filter": request.status_filter,
                "parent_filter": request.parent_filter,
                "scheme_filter": request.scheme_filter
            },
            requesting_user_context={
                "role": requesting_role,
                "user_id": current_user.id,
                "name": current_user.full_name
            },
            hierarchy_info={
                "total_manageable": total,
                "current_level": ROLE_HIERARCHY[requesting_role]["level"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error in role-based member listing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get member list"
        )

def get_user_hierarchy_ids(user_id: int, db: Session) -> List[int]:
    """Get all user IDs in the hierarchy under a specific user"""
    def get_children_recursive(parent_id: int) -> List[int]:
        children = db.query(User.id).filter(User.parent_id == parent_id).all()
        child_ids = [child.id for child in children]
        
        for child_id in child_ids.copy():
            child_ids.extend(get_children_recursive(child_id))
        
        return child_ids
    
    return get_children_recursive(user_id)
        
    #     search_term = f"%{q}%"
    #     members = db.query(User).filter(
    #         User.role.has(Role.name.in_(manageable_roles)),
    #         (User.full_name.ilike(search_term)) |
    #         (User.user_code.ilike(search_term)) |
    #         (User.email.ilike(search_term)) |
    #         (User.phone.ilike(search_term))
    #     ).limit(limit).all()
        
    #     results = []
    #     for member in members:
    #         results.append({
    #             "id": member.id,
    #             "user_code": member.user_code,
    #             "full_name": member.full_name,
    #             "role": member.role.name,
    #             "email": member.email,
    #             "phone": member.phone,
    #             "is_active": member.is_active
    #         })
        
    #     return {
    #         "success": True,
    #         "results": results,
    #         "total": len(results)
    #     }
        
    # except Exception as e:
    #     logger.error(f"Error in member search: {str(e)}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Failed to search members"
    #     )