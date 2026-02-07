#!/usr/bin/env python3
"""
Superadmin Initialization Script
This script creates the superadmin user in the database using credentials from .env file.
"""

import sys
import os
import logging
from sqlalchemy.orm import Session

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal, engine
from database.init_db import init_superadmin
from config.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to initialize superadmin user."""
    try:
        # Get settings from .env file
        settings = get_settings()
        
        logger.info("=== Superadmin Initialization Script ===")
        logger.info(f"User Code: {settings.SUPERADMIN_USER_CODE}")
        logger.info(f"Username: {settings.SUPERADMIN_USERNAME}")
        logger.info(f"Email: {settings.SUPERADMIN_EMAIL}")
        logger.info(f"Phone: {settings.SUPERADMIN_PHONE}")
        logger.info(f"Full Name: {settings.SUPERADMIN_NAME}")
        
        # Create database session
        with SessionLocal() as db:
            logger.info("Initializing superadmin user...")
            init_superadmin(db)
            logger.info("✅ Superadmin initialization completed successfully!")
            
        # Verify the superadmin was created
        with SessionLocal() as db:
            from services.models.models import User, Role
            
            superadmin = db.query(User).filter(
                User.user_code == settings.SUPERADMIN_USER_CODE
            ).first()
            
            if superadmin:
                logger.info("✅ Superadmin user verification:")
                logger.info(f"   - ID: {superadmin.id}")
                logger.info(f"   - User Code: {superadmin.user_code}")
                logger.info(f"   - Username: {superadmin.username}")
                logger.info(f"   - Email: {superadmin.email}")
                logger.info(f"   - Phone: {superadmin.phone}")
                logger.info(f"   - Full Name: {superadmin.full_name}")
                logger.info(f"   - Role: {superadmin.role.name}")
                logger.info(f"   - Active: {superadmin.is_active}")
                logger.info(f"   - Has Password: {'Yes' if superadmin.hashed_password else 'No'}")
            else:
                logger.error("❌ Superadmin user was not found after creation!")
                return False
                
        logger.info("=== Superadmin Login Credentials ===")
        logger.info(f"Email/Username: {settings.SUPERADMIN_EMAIL}")
        logger.info(f"User Code: {settings.SUPERADMIN_USER_CODE}")
        logger.info(f"Password: {settings.SUPERADMIN_PASSWORD}")
        logger.info("==========================================")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during superadmin initialization: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)