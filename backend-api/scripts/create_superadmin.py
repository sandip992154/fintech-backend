import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database import get_db, Base
from passlib.context import CryptContext
from services.models.models import User, Role

from config.config import settings
from database.dbmodels.get_use_details import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_superadmin(db=None):
    # If no db session provided, create one
    if db is None:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        should_close_db = True
    else:
        should_close_db = False

    try:
        # First check if super_admin role exists
        super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
        if not super_admin_role:
            # Create super_admin role
            super_admin_role = Role(
                name="super_admin",
                description="Super Administrator with full system access"
            )
            db.add(super_admin_role)
            db.commit()
            print("Created super_admin role")

        # Check if superadmin user already exists
        existing_superadmin = db.query(User).join(Role).filter(Role.name == "super_admin").first()
        if existing_superadmin:
            print("Superadmin already exists!")
            return

        import uuid
        # Create new superadmin user
        superadmin = User(
            user_code=f"SA{uuid.uuid4().hex[:8].upper()}",  # Generate unique user code
            username=settings.SUPERADMIN_USERNAME,
            email=settings.SUPERADMIN_EMAIL,
            phone=settings.SUPERADMIN_PHONE,
            hashed_password=pwd_context.hash(settings.SUPERADMIN_PASSWORD),
            full_name=settings.SUPERADMIN_NAME,
            role_id=super_admin_role.id,
            is_active=True
        )

        # Add to database
        db.add(superadmin)
        db.commit()
        print("Superadmin created successfully!")

    except Exception as e:
        print(f"Error creating superadmin: {e}")
        db.rollback()
    finally:
        if should_close_db:
            db.close()

    return True

if __name__ == "__main__":
    create_superadmin()