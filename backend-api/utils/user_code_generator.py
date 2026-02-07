"""
Centralized User Code Generation Utility
Provides unified user code generation across all systems
"""
from sqlalchemy.orm import Session
from config.constants import ROLE_PREFIX_MAP
from services.models.models import User


def generate_unique_user_code(role: str, db: Session) -> str:
    """
    Generate unique user code using auth system's sequential format
    Format: {PREFIX}{5_DIGIT_SEQUENTIAL}
    This maintains consistency with existing auth system
    """
    # Get prefix from constants
    prefix = ROLE_PREFIX_MAP.get(role, "BANDCUS")
    
    # Find the last user with this prefix (auth system approach)
    last_user = db.query(User).filter(
        User.user_code.like(f"{prefix}%")
    ).order_by(User.id.desc()).first()
    
    # Calculate next sequential number
    last_num = 0
    if last_user and last_user.user_code:
        try:
            # Extract numeric part from user_code
            last_num = int(last_user.user_code.replace(prefix, ""))
        except (ValueError, TypeError):
            last_num = 0
    
    # Generate new sequential user code
    user_code = f"{prefix}{last_num + 1:05d}"
    
    return user_code


def validate_user_code_format(user_code: str) -> bool:
    """
    Validate if user code follows the expected format
    """
    if not user_code or len(user_code) < 8:
        return False
    
    # Check if prefix exists in our mapping
    for prefix in ROLE_PREFIX_MAP.values():
        if user_code.startswith(prefix):
            # Check if remaining part is numeric
            suffix = user_code[len(prefix):]
            return suffix.isdigit() and len(suffix) == 5
    
    return False