#!/usr/bin/env python3
"""
Superadmin User Management Script
This script checks existing superadmin users and creates/updates them as needed.
"""

import sys
import os
import logging
from sqlalchemy.orm import Session

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from services.models.models import User, Role
from utils.security import get_password_hash
from config.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_existing_superadmin(db: Session, settings):
    """Check for existing superadmin users."""
    
    # Check by user_code
    user_by_code = db.query(User).filter(
        User.user_code == settings.SUPERADMIN_USER_CODE
    ).first()
    
    # Check by email
    user_by_email = db.query(User).filter(
        User.email == settings.SUPERADMIN_EMAIL
    ).first()
    
    # Check for any super_admin role users
    super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
    users_with_super_admin_role = []
    if super_admin_role:
        users_with_super_admin_role = db.query(User).filter(
            User.role_id == super_admin_role.id
        ).all()
    
    return {
        "user_by_code": user_by_code,
        "user_by_email": user_by_email,
        "super_admin_role": super_admin_role,
        "users_with_super_admin_role": users_with_super_admin_role
    }

def create_or_update_superadmin(db: Session, settings):
    """Create or update superadmin user."""
    
    # Ensure super_admin role exists
    super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
    if not super_admin_role:
        logger.info("Creating super_admin role...")
        super_admin_role = Role(
            name="super_admin",
            description="Super Administrator with full system access"
        )
        db.add(super_admin_role)
        db.commit()
        logger.info("✅ Super admin role created successfully")
    
    existing = check_existing_superadmin(db, settings)
    
    # Case 1: User with desired user_code exists
    if existing["user_by_code"]:
        user = existing["user_by_code"]
        logger.info(f"Found existing user with user_code {settings.SUPERADMIN_USER_CODE}")
        logger.info(f"Current email: {user.email}")
        logger.info(f"Desired email: {settings.SUPERADMIN_EMAIL}")
        
        if user.email != settings.SUPERADMIN_EMAIL:
            # Check if the desired email is used by another user
            if existing["user_by_email"] and existing["user_by_email"].id != user.id:
                logger.warning(f"Email {settings.SUPERADMIN_EMAIL} is used by another user (ID: {existing['user_by_email'].id})")
                logger.info("Updating existing user with user_code instead of creating new one")
            
            # Update the existing user with user_code
            user.email = settings.SUPERADMIN_EMAIL
            user.username = settings.SUPERADMIN_USERNAME
            user.phone = settings.SUPERADMIN_PHONE
            user.full_name = settings.SUPERADMIN_NAME
            user.hashed_password = get_password_hash(settings.SUPERADMIN_PASSWORD)
            user.role_id = super_admin_role.id
            user.is_active = True
            
            db.commit()
            logger.info("✅ Updated existing superadmin user")
            return user
    
    # Case 2: User with desired email exists but different user_code
    elif existing["user_by_email"]:
        user = existing["user_by_email"]
        logger.info(f"Found existing user with email {settings.SUPERADMIN_EMAIL}")
        logger.info(f"Current user_code: {user.user_code}")
        logger.info(f"Desired user_code: {settings.SUPERADMIN_USER_CODE}")
        
        # Update the existing user
        user.user_code = settings.SUPERADMIN_USER_CODE
        user.username = settings.SUPERADMIN_USERNAME
        user.phone = settings.SUPERADMIN_PHONE
        user.full_name = settings.SUPERADMIN_NAME
        user.hashed_password = get_password_hash(settings.SUPERADMIN_PASSWORD)
        user.role_id = super_admin_role.id
        user.is_active = True
        
        db.commit()
        logger.info("✅ Updated existing user to be superadmin")
        return user
    
    # Case 3: No user exists, create new one
    else:
        logger.info("No existing superadmin user found, creating new one...")
        user = User(
            user_code=settings.SUPERADMIN_USER_CODE,
            username=settings.SUPERADMIN_USERNAME,
            email=settings.SUPERADMIN_EMAIL,
            phone=settings.SUPERADMIN_PHONE,
            hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
            full_name=settings.SUPERADMIN_NAME,
            role_id=super_admin_role.id,
            is_active=True
        )
        db.add(user)
        db.commit()
        logger.info("✅ Created new superadmin user")
        return user

def main():
    """Main function."""
    try:
        settings = get_settings()
        
        logger.info("=== Superadmin User Management Script ===")
        logger.info(f"Target User Code: {settings.SUPERADMIN_USER_CODE}")
        logger.info(f"Target Username: {settings.SUPERADMIN_USERNAME}")
        logger.info(f"Target Email: {settings.SUPERADMIN_EMAIL}")
        logger.info(f"Target Phone: {settings.SUPERADMIN_PHONE}")
        logger.info(f"Target Full Name: {settings.SUPERADMIN_NAME}")
        
        with SessionLocal() as db:
            logger.info("\n--- Checking existing users ---")
            existing = check_existing_superadmin(db, settings)
            
            if existing["users_with_super_admin_role"]:
                logger.info(f"Found {len(existing['users_with_super_admin_role'])} users with super_admin role:")
                for user in existing["users_with_super_admin_role"]:
                    logger.info(f"  - ID: {user.id}, Code: {user.user_code}, Email: {user.email}, Name: {user.full_name}")
            else:
                logger.info("No users with super_admin role found")
            
            if existing["user_by_code"]:
                logger.info(f"User with target user_code exists: {existing['user_by_code'].email}")
            
            if existing["user_by_email"]:
                logger.info(f"User with target email exists: {existing['user_by_email'].user_code}")
            
            logger.info("\n--- Creating/Updating superadmin ---")
            superadmin = create_or_update_superadmin(db, settings)
            
            logger.info("\n--- Final superadmin user details ---")
            logger.info(f"✅ Superadmin user details:")
            logger.info(f"   - ID: {superadmin.id}")
            logger.info(f"   - User Code: {superadmin.user_code}")
            logger.info(f"   - Username: {superadmin.username}")
            logger.info(f"   - Email: {superadmin.email}")
            logger.info(f"   - Phone: {superadmin.phone}")
            logger.info(f"   - Full Name: {superadmin.full_name}")
            logger.info(f"   - Role: {superadmin.role.name}")
            logger.info(f"   - Active: {superadmin.is_active}")
            
            logger.info("\n=== Login Credentials ===")
            logger.info(f"Email/Username: {superadmin.email}")
            logger.info(f"User Code: {superadmin.user_code}")
            logger.info(f"Password: {settings.SUPERADMIN_PASSWORD}")
            logger.info("==========================")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)