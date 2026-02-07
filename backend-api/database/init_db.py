from sqlalchemy.orm import Session
from services.models.models import User, Role
from services.models.superadmin_model import SuperAdmin
from services.models.user_models import KYCDocument, MPIN, UserProfile, OTP
from config.config import settings
from utils.security import get_password_hash
import logging

# Configure logging
logger = logging.getLogger(__name__)

def init_roles(db: Session) -> None:
    """Initialize all system roles if they don't exist."""
    try:
        logger.info("=== INITIALIZING SYSTEM ROLES ===")
        
        # Define all system roles with their descriptions and hierarchy levels
        roles_data = [
            {
                "name": "super_admin",
                "description": "Super Administrator with full system access",
                "level": 0  # Highest level
            },
            {
                "name": "admin", 
                "description": "System Administrator with administrative privileges",
                "level": 1
            },
            {
                "name": "whitelabel",
                "description": "White Label Partner - Top tier business partner",
                "level": 2
            },
            {
                "name": "mds",
                "description": "Master Distributor - Regional business head",
                "level": 3
            },
            {
                "name": "distributor",
                "description": "Distributor - Area business manager",
                "level": 4
            },
            {
                "name": "retailer",
                "description": "Retailer - Direct service provider",
                "level": 5
            },
            {
                "name": "customer",
                "description": "End Customer - Service consumer",
                "level": 6  # Lowest level
            },
            {
                "name": "employee",
                "description": "Company Employee - Internal staff member",
                "level": 1  # Same as admin level but different permissions
            },
            {
                "name": "support",
                "description": "Customer Support - Help desk and assistance",
                "level": 2  # Can assist customers and lower tiers
            }
        ]
        
        created_roles = []
        updated_roles = []
        
        for role_data in roles_data:
            # Check if role already exists
            existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
            
            if existing_role:
                # Update existing role if description changed
                if existing_role.description != role_data["description"]:
                    existing_role.description = role_data["description"]
                    updated_roles.append(role_data["name"])
                logger.info(f"Role '{role_data['name']}' already exists")
            else:
                # Create new role
                new_role = Role(
                    name=role_data["name"],
                    description=role_data["description"]
                )
                db.add(new_role)
                created_roles.append(role_data["name"])
                logger.info(f"Created role: {role_data['name']}")
        
        # Commit all role changes
        if created_roles or updated_roles:
            db.commit()
            
        if created_roles:
            logger.info(f"✅ Created {len(created_roles)} new roles: {', '.join(created_roles)}")
        if updated_roles:
            logger.info(f"✅ Updated {len(updated_roles)} roles: {', '.join(updated_roles)}")
            
        # Log final role count
        total_roles = db.query(Role).count()
        logger.info(f"✅ Total roles in system: {total_roles}")
        logger.info("=== ROLES INITIALIZATION COMPLETED ===")
        
    except Exception as e:
        logger.error(f"❌ Error initializing roles: {str(e)}")
        db.rollback()
        raise

def init_superadmin(db: Session) -> None:
    """Initialize the superadmin user and role if they don't exist."""
    try:
        logger.info("=== INITIALIZING SUPERADMIN ===")
        
        # First, initialize all system roles
        init_roles(db)
        
        # Get the super_admin role (should exist after init_roles)
        super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
        if not super_admin_role:
            logger.error("Super admin role not found after role initialization!")
            raise Exception("Failed to create super_admin role")

        # Check for existing superadmin by user_code first
        superadmin = db.query(User).filter(
            User.user_code == settings.SUPERADMIN_USER_CODE
        ).first()

        if superadmin:
            logger.info(f"Superadmin user with user_code {settings.SUPERADMIN_USER_CODE} already exists")
            # Update password and ensure correct role
            superadmin.hashed_password = get_password_hash(settings.SUPERADMIN_PASSWORD)
            superadmin.role_id = super_admin_role.id
            superadmin.is_active = True
            db.commit()
            logger.info("Updated existing superadmin user password and role")
            return

        # Check for existing user by email
        existing_user_by_email = db.query(User).filter(
            User.email == settings.SUPERADMIN_EMAIL
        ).first()

        if existing_user_by_email:
            logger.info(f"User with email {settings.SUPERADMIN_EMAIL} exists, updating to superadmin...")
            # Update existing user to be superadmin
            existing_user_by_email.user_code = settings.SUPERADMIN_USER_CODE
            existing_user_by_email.username = settings.SUPERADMIN_USERNAME
            existing_user_by_email.phone = settings.SUPERADMIN_PHONE
            existing_user_by_email.full_name = settings.SUPERADMIN_NAME
            existing_user_by_email.hashed_password = get_password_hash(settings.SUPERADMIN_PASSWORD)
            existing_user_by_email.role_id = super_admin_role.id
            existing_user_by_email.is_active = True
            db.commit()
            logger.info(f"Updated existing user to superadmin with user_code: {settings.SUPERADMIN_USER_CODE}")
            return

        # Create new superadmin user if none exists
        logger.info("Creating new superadmin user...")
        superadmin = User(
            user_code=settings.SUPERADMIN_USER_CODE,
            username=settings.SUPERADMIN_USERNAME,
            email=settings.SUPERADMIN_EMAIL,
            phone=settings.SUPERADMIN_PHONE,
            hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
            full_name=settings.SUPERADMIN_NAME,
            role_id=super_admin_role.id,
            is_active=True
        )
        db.add(superadmin)
        db.commit()
        logger.info(f"Superadmin user created successfully with user_code: {settings.SUPERADMIN_USER_CODE}")

    except Exception as e:
        logger.error(f"Error creating superadmin: {str(e)}")
        db.rollback()
        raise