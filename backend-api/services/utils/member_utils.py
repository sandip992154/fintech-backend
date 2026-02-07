"""
Member Management Utilities
Centralized helper functions for member operations
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from services.models.models import User, Role
from services.schemas.member_schema import MemberOut
from config.constants import ROLE_HIERARCHY
import logging

logger = logging.getLogger(__name__)

# ======================== Phone Number Utilities ========================

def normalize_phone(phone_str: Optional[str]) -> Optional[str]:
    """
    Normalize phone numbers to handle international format
    Removes +91 prefix and standardizes format
    """
    if not phone_str:
        return phone_str
    
    # Remove spaces, dashes, and other formatting characters
    clean_phone = ''.join(filter(str.isdigit, phone_str))
    
    # Remove +91 prefix if present
    if phone_str.startswith('+91'):
        clean_phone = clean_phone[2:] if len(clean_phone) > 10 else clean_phone
    
    # Remove 91 prefix if it's a 12-digit number
    elif clean_phone.startswith('91') and len(clean_phone) == 12:
        clean_phone = clean_phone[2:]
    
    return clean_phone

# ======================== Role Hierarchy Utilities ========================

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

# ======================== Member Data Conversion ========================

def create_member_out(member: User) -> MemberOut:
    """
    Create standardized MemberOut object from User model
    Centralizes member data conversion logic
    """
    # Get parent name if parent exists
    parent_name = None
    if member.parent_id and member.parent:
        parent_name = member.parent.full_name
    
    return MemberOut(
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
        company_pan_card=getattr(member, 'company_pan_card', None),
        aadhaar_card_number=member.aadhaar_card_number,
        role=member.role.name,
        role_id=member.role_id,
        role_name=member.role.name,
        parent_id=member.parent_id,
        parent_name=parent_name,
        is_active=member.is_active,
        created_at=member.created_at,
        updated_at=member.updated_at,
        kyc_status="not_submitted",  # Default value
        profile_complete=bool(member.pan_card_number and member.aadhaar_card_number),
        children_count=0  # Default value - could be calculated if needed
    )

# ======================== Parent Assignment Logic ========================

def determine_parent_id(member_data, current_user: User, db: Session) -> Optional[int]:
    """
    Determine the correct parent_id for a new member based on role hierarchy
    Centralizes parent assignment logic
    """
    # If parent_id is explicitly provided, validate and use it
    if hasattr(member_data, 'parent_id') and member_data.parent_id:
        parent_user = db.query(User).filter(User.id == member_data.parent_id).first()
        if parent_user:
            return member_data.parent_id
    
    # Auto-assign parent for specific roles
    if member_data.role_name == "Admin":
        # Auto-assign SuperAdmin as parent for Admin
        superadmin = db.query(User).join(Role).filter(Role.name == "SuperAdmin").first()
        if superadmin:
            return superadmin.id
    
    elif member_data.role_name == "WhiteLabel":
        # Auto-assign Admin as parent for WhiteLabel
        admin_user = db.query(User).join(Role).filter(Role.name == "Admin").first()
        if admin_user:
            return admin_user.id
    
    # Default: current user as parent
    return current_user.id

# ======================== Query Builders ========================

def build_member_query(db: Session, current_user: User, role_filter: Optional[str] = None,
                      is_active: Optional[bool] = None, search: Optional[str] = None):
    """
    Build base query for member listing with common filters
    """
    # Base query with role join
    query = db.query(User).join(Role)
    
    # Filter by manageable roles
    manageable_roles = get_manageable_roles(current_user.role.name)
    if manageable_roles:
        query = query.filter(Role.name.in_(manageable_roles))
    
    # Apply role filter
    if role_filter:
        query = query.filter(Role.name == role_filter)
    
    # Apply active status filter
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.phone.ilike(search_term)) |
            (User.user_code.ilike(search_term))
        )
    
    return query

# ======================== Validation Utilities ========================

def validate_member_data(member_data) -> Dict[str, Any]:
    """
    Validate member data and return validation results
    """
    import re
    
    errors = []
    warnings = []
    
    # Validate required fields
    if not member_data.full_name or not member_data.full_name.strip():
        errors.append("Full name is required")
    elif len(member_data.full_name.strip()) < 2:
        errors.append("Full name must be at least 2 characters")
    
    if not member_data.email or not member_data.email.strip():
        errors.append("Email is required")
    else:
        # Enhanced email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, member_data.email.strip()):
            errors.append("Invalid email format")
    
    # Validate phone number format
    if not member_data.phone:
        errors.append("Phone number is required")
    else:
        normalized = normalize_phone(member_data.phone)
        if len(normalized) != 10:
            errors.append("Phone number must be 10 digits")
        elif not normalized.isdigit():
            errors.append("Phone number must contain only digits")
    
    # Validate role name
    if not hasattr(member_data, 'role_name') or not member_data.role_name:
        errors.append("Role name is required")
    
    # Validate PAN card format (if provided)
    if hasattr(member_data, 'pan_card_number') and member_data.pan_card_number:
        pan = member_data.pan_card_number.upper().strip()
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pan_pattern, pan):
            errors.append("Invalid PAN card format (should be ABCDE1234F)")
    
    # Validate Aadhaar number format (if provided)
    if hasattr(member_data, 'aadhaar_card_number') and member_data.aadhaar_card_number:
        aadhaar = member_data.aadhaar_card_number.replace(' ', '').replace('-', '')
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            errors.append("Aadhaar number must be 12 digits")
    
    # Validate PIN code (if provided)
    if hasattr(member_data, 'pin_code') and member_data.pin_code:
        pin_code = str(member_data.pin_code).strip()
        if len(pin_code) != 6 or not pin_code.isdigit():
            errors.append("PIN code must be 6 digits")
    
    # Validate company PAN card format (if provided)
    if hasattr(member_data, 'company_pan_card') and member_data.company_pan_card:
        company_pan = member_data.company_pan_card.upper()
        if len(company_pan) != 10:
            errors.append("Company PAN card number must be 10 characters")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

# ======================== Logging Helpers ========================

def log_member_action(action: str, member_code: str, user_code: str, details: str = ""):
    """
    Standardized logging for member actions
    """
    logger.info(f"Member {action}: {member_code} by {user_code} {details}".strip())

def log_member_error(action: str, member_code: str, user_code: str, error: str):
    """
    Standardized error logging for member actions
    """
    logger.error(f"Member {action} failed: {member_code} by {user_code} - {error}")