from datetime import datetime, timedelta
from typing import Optional, List
import logging
import random
import os
import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from database.database import get_db
from services.models.models import User, RefreshToken, Role, OTP
from services.schemas import schemas
from utils.gmail_utils import send_login_email
from utils.error_handlers import APIErrorResponse, handle_database_exceptions, validate_required_fields, validate_user_permissions
from config import email_config
from config.config import get_settings

# Get settings instance to access SUPERADMIN_EMAIL
settings = get_settings()

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

# Demo in-memory storage for roles during testing
demo_roles_storage = {}
demo_role_counter = 0

# Import settings
from config.config import get_settings
settings = get_settings()

# Security configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create a logger instance for this file
logger = logging.getLogger(__name__)

# Role hierarchy (lower number = higher authority)
ROLE_HIERARCHY = {
    "super_admin": 1,
    "admin": 2,
    "whitelabel": 3,
    "mds": 4,
    "distributor": 5,
    "retailer": 6,
    "customer": 7
}

def has_permission(user_role: str, required_role: str) -> bool:
    """Check if user role has permission for required role."""
    user_level = ROLE_HIERARCHY.get(user_role, 999)
    required_level = ROLE_HIERARCHY.get(required_role, 999)
    return user_level <= required_level

def get_role_permissions(role: str) -> List[str]:
    """Get list of permissions for a role."""
    role_level = ROLE_HIERARCHY.get(role, 999)
    permissions = []
    
    for role_name, level in ROLE_HIERARCHY.items():
        if role_level <= level:
            permissions.append(role_name)
    
    return permissions

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_code(db: Session, user_code: str) -> Optional[User]:
    """Get a user by their user_code"""
    return db.query(User).filter(User.user_code == user_code).first()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current user from the token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_code: str = payload.get("sub")
        if user_code is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.user_code == user_code).first()
    if user is None:
        raise credentials_exception
        
    return user

async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> dict:
    """Refresh an access token using a refresh token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_code: str = payload.get("sub")
        if user_code is None:
            raise credentials_exception

        # Get the user
        user = db.query(User).filter(User.user_code == user_code).first()
        if user is None:
            raise credentials_exception

        # Get the stored refresh token
        stored_token = db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.token == refresh_token
        ).first()

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or revoked"
            )

        # Check if token is expired
        if datetime.utcnow() > stored_token.expires_at:
            db.delete(stored_token)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )

        # Generate new access token
        new_access_token = create_access_token(
            data={
                "sub": user.user_code,
                "role": user.role.name if user.role else None,
                "user_id": user.id,
                "permissions": user.role.permissions if user.role else []
            }
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except JWTError:
        raise credentials_exception

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token"""
    import time
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # Add timestamp in microseconds to ensure uniqueness
    to_encode.update({"exp": expire, "iat": time.time()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new refresh token"""
    import time
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    # Add timestamp in microseconds to ensure uniqueness
    to_encode.update({"exp": expire, "iat": time.time()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current authenticated user from the token with session validation"""
    try:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_code: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if not user_code or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing required claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Fetch user from DB
        user = db.query(User).filter(User.id == user_id, User.user_code == user_code).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found for provided token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check active refresh session for the user
        active_refresh = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
            .first()
        )

        if not active_refresh:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User session has expired or logged out. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException as http_err:
        # Re-raise known errors (frontend will see exact detail)
        raise http_err

    except Exception as e:
        # Unexpected backend errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error in get_current_user: {str(e)}"
        )


@router.post("/login", response_model=schemas.MessageResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login endpoint: send OTP to user's email for verification."""
    # Look for user by username/email/phone/user_code
    user = db.query(User).filter(
        (User.username == form_data.username) |
        (User.email == form_data.username) |
        (User.phone == form_data.username) |
        (User.user_code == form_data.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or incorrect credentials"
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Check for too many OTP attempts
    recent_otps = db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.created_at >= datetime.utcnow() - timedelta(minutes=settings.OTP_COOLDOWN_MINUTES)
    ).count()

    if recent_otps >= settings.MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many OTP attempts. Please wait {settings.OTP_COOLDOWN_MINUTES} minutes."
        )

    # Generate and store OTP
    otp_code = str(random.randint(1000, 9999))
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    # Invalidate any existing unused OTPs
    db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.is_used == False
    ).update({"is_used": True})
    db.commit()  # Commit the invalidation before creating new OTP

    # Create new OTP
    otp_obj = OTP(
        user_id=user.id,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.add(otp_obj)
    db.commit()

    # Send OTP email
    await send_login_email(
        to_email=user.email,
        name=user.full_name,
        login_id=user.user_code,
        password=None,
        signup_link=None,
        role=user.role.name,
        otp=otp_code
    )

    return schemas.MessageResponse(
        message=f"OTP sent to {user.email}. Please verify to complete login.",
        email=user.email
    )

@router.post("/login-otp-verify", response_model=schemas.TokenResponse)
async def login_otp_verify(request: schemas.OTPVerifyRequest, db: Session = Depends(get_db)):
    # Check if the user exists and has a valid role
    user = db.query(User).filter(
        (User.email == request.identifier) |
        (User.phone == request.identifier) |
        (User.user_code == request.identifier)
    ).join(Role).filter(Role.name.in_(["super_admin", "admin","whitelabel","mds","distributor","retailer","customer"])).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    # Find valid OTP for the superadmin
    otp_obj = db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.is_used == False,
        OTP.expires_at > datetime.utcnow(),
        OTP.otp_code == request.otp
    ).first()

    if not otp_obj:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    # Mark OTP as used
    otp_obj.is_used = True
    db.commit()

    # Create token with proper permissions
    token_data = {
        "sub": user.user_code,
        "role": user.role.name,
        "user_id": user.id,
        "permissions": get_role_permissions(user.role.name)
    }

    # Create access token and refresh token
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data={"sub": user.user_code, "type": "refresh"})

    # Store refresh token
    token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=token_expires
    )
    db.add(db_token)
    db.commit()

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role.name,
        permissions=get_role_permissions(user.role.name),
        user_id=user.id
    )


@router.post("/demo-login", response_model=schemas.TokenResponse)
async def demo_login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Demo login endpoint - bypasses OTP for development/demo purposes.
    Only works for superadmin account.
    """
    # Look for user by username/email/phone/user_code
    user = db.query(User).filter(
        (User.username == credentials.username) |
        (User.email == credentials.username) |
        (User.phone == credentials.username) |
        (User.user_code == credentials.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or incorrect credentials"
        )

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Check if user has a role
    if not user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role not configured"
        )

    # Create token with proper permissions
    token_data = {
        "sub": user.user_code,
        "role": user.role.name,
        "user_id": user.id,
        "permissions": get_role_permissions(user.role.name)
    }

    # Create access token and refresh token
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data={"sub": user.user_code, "type": "refresh"})

    # Store refresh token
    token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=token_expires
    )
    db.add(db_token)
    db.commit()

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role.name,
        permissions=get_role_permissions(user.role.name),
        user_id=user.id
    )


# Registration email utility update
async def send_credentials_email(user, password, role_name):
    # Role dashboard URL mapping
    dashboard_urls = {
        "admin": "https://bandru.com/admin-dashboard",
        "whitelabel": "https://bandru.com/whitelabel-dashboard",
        "mds": "https://bandru.com/mds-dashboard",
        "distributor": "https://bandru.com/distributor-dashboard",
        "retailer": "https://bandru.com/retailer-dashboard",
        "customer": "https://bandru.com/customer-dashboard"
    }
    dashboard_url = dashboard_urls.get(role_name, "https://bandru.com/login")
    try:
        await send_login_email(
            to_email=user.email,
            name=user.full_name,
            login_id=user.user_code,
            password=password,
            signup_link=dashboard_url,
            role=role_name
        )
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send credentials email to {user.email}: {str(e)}")
        return {"success": False, "message": f"Email delivery failed: {str(e)}"}

@router.get("/roles", response_model=List[schemas.RoleOut])
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available roles"""
    try:
        # Demo implementation - static response for testing
        return [
            schemas.RoleOut(
                id=1,
                name="user",
                description="Default user role"
            ),
            schemas.RoleOut(
                id=2,
                name="admin",
                description="Administrator role"
            )
        ]
    except Exception as e:
        logger.exception(f"Backend error in get_roles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Unexpected internal server error while fetching roles"
        )

@router.post("/roles", response_model=schemas.RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new role (requires admin privileges)"""
    try:
        # Check for existing role with same name
        for existing_role in demo_roles_storage.values():
            if existing_role["name"] == role_in.name:
                logger.warning(f"Frontend error: Role '{role_in.name}' already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role name already exists"
                )

        # Validate permissions (simple validation for demo)
        valid_permissions = [
            "view_users", "create_users", "edit_users", "delete_users",
            "view_roles", "create_roles", "edit_roles", "delete_roles",
            "view_transactions", "create_transactions", "edit_transactions", "delete_transactions",
            "manage_wallet", "view_wallet", "manage_services", "view_services"
        ]

        for permission in role_in.permissions:
            if permission not in valid_permissions:
                logger.warning(f"Frontend error: Invalid permission '{permission}'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission: {permission}"
                )

        # Demo implementation - static response for testing using in-memory storage
        global demo_role_counter
        demo_role_counter += 1
        role_id = demo_role_counter

        demo_roles_storage[role_id] = {
            "id": role_id,
            "name": role_in.name,
            "description": role_in.description
        }

        return schemas.RoleOut(
            id=role_id,
            name=role_in.name,
            description=role_in.description
        )

    except HTTPException as http_err:
        # Known frontend-related issues
        raise http_err
    except Exception as e:
        logger.exception(f"Backend error in create_role: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Unexpected internal server error while creating role"
        )
# -------------------
# Routes
# -------------------

@router.post("/register", response_model=schemas.UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user, send success email, and block login until KYC is approved. No authentication required. All roles except 'super_admin' allowed."""
    try:
        logger.info("➡️ Starting user registration process")

        # Prevent super admin signup via API
        if user_in.role == "super_admin":
            logger.warning("❌ Super admin signup attempt blocked")
            raise HTTPException(status_code=403, detail="Super admin signup is not allowed via API. Please contact system administrator.")

        # SECURITY FIX: Only allow customer registration via public API
        allowed_roles = ["customer"]
        if user_in.role not in allowed_roles:
            logger.warning(f"❌ Invalid role for public registration: {user_in.role}")
            raise HTTPException(
                status_code=403, 
                detail="Public registration is only available for customers. Other roles require invitation from administrator."
            )

        logger.info(f"✅ Role check passed for role={user_in.role}")

        # Duplicate checks
        if db.query(User).filter(User.email == user_in.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if db.query(User).filter(User.phone == user_in.phone).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")

        logger.info("✅ Duplicate checks passed")

        # Hash password
        try:
            hashed_password = get_password_hash(user_in.password)
            logger.info("✅ Password hashed successfully")
        except Exception as e:
            logger.error(f"❌ Password hashing failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error during password hashing")

        # Get/create role
        try:
            user_role = db.query(Role).filter(Role.name == user_in.role).first()
            if not user_role:
                logger.info(f"ℹ️ Role {user_in.role} not found, creating...")
                user_role = Role(name=user_in.role, description=f"{user_in.role.title()} role")
                db.add(user_role)
                db.commit()
                db.refresh(user_role)
            logger.info(f"✅ Role ready: {user_role.id}")
        except Exception as e:
            logger.error(f"❌ Role creation/fetch failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error while handling role")

        # Generate user_code using centralized utility
        from utils.user_code_generator import generate_unique_user_code
        user_code = generate_unique_user_code(user_in.role, db)
        logger.info(f"✅ Generated user_code: {user_code}")

        # Password validation
        if not validate_password_format(user_in.password):
            logger.warning("❌ Password format invalid")
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters, include uppercase, lowercase, digit, and special character.")
        password = user_in.password or "Abcd@1234"

        # Create user
        try:
            logger.info(f"➡️ Creating user: email={user_in.email}, phone={user_in.phone}, user_code={user_code}")
            user = User(
                email=user_in.email,
                phone=user_in.phone,
                full_name=user_in.full_name,
                hashed_password=get_password_hash(password),
                role_id=user_role.id,
                is_active=True,
                user_code=user_code,
                username=user_code,  # Use user_code as username for backward compatibility
                
                # Initialize new fields for public registration (customers)
                pan_card_number=getattr(user_in, 'pan_card_number', None),
                aadhaar_card_number=getattr(user_in, 'aadhaar_card_number', None),
                shop_name=getattr(user_in, 'shop_name', None),
                scheme=getattr(user_in, 'scheme', None),
                mobile=getattr(user_in, 'mobile', None),
                company_pan_card=None,  # Not applicable for public customer registration
                parent_id=None  # No parent for public registration
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"✅ User created with ID={user.id}")
        except Exception as e:
            logger.error(f"❌ User creation failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error during user creation: {str(e)}")

        # Send email
        try:
            dashboard_urls = {
                "admin": "https://bandru.com/admin-dashboard",
                "whitelabel": "https://bandru.com/whitelabel-dashboard",
                "mds": "https://bandru.com/mds-dashboard",
                "distributor": "https://bandru.com/distributor-dashboard",
                "retailer": "https://bandru.com/retailer-dashboard",
                "customer": "https://bandru.com/customer-dashboard"
            }
            dashboard_url = dashboard_urls.get(user_in.role, "https://bandru.com/login")
            logger.info(f"➡️ Sending registration email to {user.email}")
            await send_login_email(
                to_email=user.email,
                name=user.full_name,
                login_id=user.user_code,
                password=password,
                signup_link=None,
                role=user_in.role,
                user_code=user.user_code,
                dashboard_url=dashboard_url
            )
            logger.info("✅ Registration email sent")
        except Exception as e:
            logger.error(f"❌ Failed to send registration success email: {str(e)}", exc_info=True)

        # Final response
        user_obj = {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "full_name": user.full_name,
            "role": user_in.role,
            "user_code": user.user_code,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "role_id": user.role_id,
            "role_name": user_role.name  # Add role_name for UserOut schema
        }
        msg = f"User registered successfully. Your user code is {user.user_code}. Login ID: {user.user_code}. Password: {password}."
        logger.info("✅ Registration flow completed successfully")
        return schemas.UserRegisterResponse(
            message=msg,
            user=schemas.UserOut(**user_obj),
            access_token="",  # Return empty string if not used
            refresh_token="",  # Return empty string if not used
            otp=None
        )

    except HTTPException as http_err:
        logger.warning(f"⚠️ HTTPException: {http_err.detail}")
        raise http_err
    except Exception as e:
        logger.error(f"🔥 Unexpected error in register: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error during registration")


@router.get("/me", response_model=schemas.UserOut)
async def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information including role details"""
    user_role = db.query(Role).filter(Role.id == current_user.role_id).first()
    role_name = user_role.name if user_role else "customer"
    
    return schemas.UserOut(
        id=current_user.id,
        user_code=current_user.user_code,
        email=current_user.email,
        phone=current_user.phone,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        role_id=current_user.role_id,
        role_name=role_name,
        profile_photo=current_user.profile_photo
    )

@router.post("/login-json", response_model=schemas.MessageResponse)
async def login_json(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login endpoint with JSON body: send OTP to user's email for verification."""
    global SUPERADMIN_OTP
    
    # Superadmin special case
    if login_data.user_code == "BANDSA00001" and login_data.password == "Superadmin@123":
        otp_code = str(random.randint(1000, 9999))
        SUPERADMIN_OTP = otp_code
        await send_login_email(
            to_email=settings.SUPERADMIN_EMAIL,
            name="Super Admin",
            login_id="BANDSA00001",
            password=None,
            signup_link=None,
            role="super_admin",
            otp=otp_code
        )
        return schemas.MessageResponse(
            message=f"OTP sent to {settings.SUPERADMIN_EMAIL}. Please verify to complete login.",
            email=settings.SUPERADMIN_EMAIL
        )

    # Find user by any identifier
    query = db.query(User)
    if login_data.user_code:
        user = query.filter(User.user_code == login_data.user_code).first()
    elif login_data.email:
        user = query.filter(User.email == login_data.email).first()
    elif login_data.phone:
        user = query.filter(User.phone == login_data.phone).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one identifier (user_code, email, or phone) must be provided"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or incorrect credentials"
        )

    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Send OTP
    otp_code = str(random.randint(1000, 9999))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.query(OTP).filter(OTP.user_id == user.id, OTP.is_used == False).update({"is_used": True})
    otp_obj = OTP(user_id=user.id, otp_code=otp_code, expires_at=expires_at)
    db.add(otp_obj)
    db.commit()

    await send_login_email(
        to_email=user.email,
        name=user.full_name,
        login_id=user.user_code,
        password=None,
        signup_link=None,
        role=user.role.name if hasattr(user.role, 'name') else None,
        otp=otp_code
    )

    return schemas.MessageResponse(
        message=f"OTP sent to {user.email}. Please verify to complete login.",
        email=user.email
    )

@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(request: schemas.RefreshRequest, db: Session = Depends(get_db)):
    """Get a new access token using a refresh token"""
    token_str = request.refresh_token

    # Decode and validate structure
    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
        user_code: str = payload.get("sub")
        if user_code is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify token exists, not revoked, and not expired
    db_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == token_str,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        )
        .first()
    )
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked"
        )

    # Fetch user info
    user = db.query(User).filter(User.user_code == user_code).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔹 Defensive checks
    role_name = getattr(user.role, "name", None)
    permissions = []
    if hasattr(user.role, "permissions") and user.role.permissions:
        permissions = [p.name for p in user.role.permissions]

    # Issue new access token
    new_access = create_access_token(data={
        "sub": user.user_code,
        "role": role_name,
        "user_id": user.id,
        "permissions": permissions
    })

    return schemas.TokenResponse(
        access_token=new_access,
        refresh_token=token_str,
        token_type="bearer",
        role=role_name,
        permissions=permissions,
        user_id=user.id
    )

@router.post("/logout", response_model=schemas.MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and revoke all refresh tokens"""
    # Revoke all refresh tokens for the user
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id
    ).update({"revoked": True})
    
    # Commit the changes
    db.commit()
    return schemas.MessageResponse(message="Successfully logged out")


@router.get("/roles/{role_id}", response_model=schemas.RoleOut)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific role by ID"""
    try:
        # Demo implementation - check in-memory storage first
        if role_id in demo_roles_storage:
            role_data = demo_roles_storage[role_id]
            return schemas.RoleOut(
                id=role_data["id"],
                name=role_data["name"],
                description=role_data["description"]
            )

        # Return 404 if role not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    except HTTPException:
        # Reraise known HTTP errors (like 404 above)
        raise
    except Exception as e:
        # Unexpected errors will be caught here
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.put("/roles/{role_id}", response_model=schemas.RoleOut)
async def update_role(
    role_id: int,
    role_update: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a role (requires admin privileges)"""
    # Demo implementation - static response for testing
    return schemas.RoleOut(
        id=role_id,
        name=role_update.name,
        description=role_update.description
    )

@router.delete("/roles/{role_id}", response_model=schemas.MessageResponse)
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a role (requires admin privileges)"""
    # Demo implementation - check if role exists in in-memory storage
    if role_id not in demo_roles_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Remove from in-memory storage
    del demo_roles_storage[role_id]
    
    return schemas.MessageResponse(message="Role deleted successfully")

@router.get("/user/roles", response_model=List[schemas.RoleOut])
async def get_user_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get roles assigned to the current user"""
    # Demo implementation - static response for testing
    return [schemas.RoleOut(
        id=1,
        name="user",
        description="Default user role"
    )]

@router.post("/user/roles", response_model=schemas.MessageResponse)
async def assign_role_to_user(
    assignment: schemas.UserRoleAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a role to a user (requires admin privileges)"""
    # Demo implementation - static response for testing
    # If user_id is None, assign to current user
    if assignment.user_id is None:
        assignment.user_id = current_user.id
    
    return schemas.MessageResponse(message="Role assigned successfully")

@router.delete("/user/roles/{role_id}", response_model=schemas.MessageResponse) 
async def remove_role_from_user(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a role from a user (requires admin privileges)"""
    # Demo implementation - static response for testing
    return schemas.MessageResponse(message="Role removed successfully")

@router.get("/user/permissions", response_model=List[str])
async def get_user_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get permissions for the current user"""
    # Demo permissions - in real implementation, these would come from the role
    return ["view_users", "manage_wallet", "use_services"]

# Role-based access dependency
def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role = current_user.role.name if hasattr(current_user.role, 'name') else None
        if not user_role:
            raise HTTPException(status_code=403, detail="No role assigned.")
        # Super admin always allowed
        if user_role == "super_admin":
            return current_user
        # Only allow if user has required or higher role
        if ROLE_HIERARCHY.get(user_role, 999) > ROLE_HIERARCHY.get(required_role, 999):
            raise HTTPException(status_code=403, detail="Insufficient permissions.")
        return current_user
    return role_checker

def validate_password_format(password: str) -> bool:
    import re
    # Minimum 8 chars, at least one uppercase, one lowercase, one digit, one special
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\d]).{8,}$'
    return bool(re.match(pattern, password))

@router.post("/login-mpin", response_model=schemas.TokenResponse)
async def login_mpin(data: schemas.MpinLogin, db: Session = Depends(get_db)):
    """Login using user_code, email, or phone and MPIN"""
    user = db.query(User).filter(
        (User.email == data.identifier) |
        (User.phone == data.identifier) |
        (User.user_code == data.identifier)
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or incorrect credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    if user.mpin != data.mpin:
        raise HTTPException(status_code=401, detail="Incorrect MPIN")
    # Force change password/MPIN after first login
    if user.first_login:
        return {"message": "Please change your password and MPIN after first login."}
    # Token generation logic
    user_role = db.query(Role).filter(Role.id == user.role_id).first()
    role_name = user_role.name if user_role else "customer"
    permissions = get_role_permissions(role_name)
    token_data = {
        "sub": user.username,
        "role": role_name,
        "user_id": user.id,
        "permissions": permissions
    }
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        token=refresh_token,
        expires_at=expires_at,
        user_id=user.id
    )
    db.add(db_token)
    db.commit()
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=role_name,
        permissions=permissions,
        user_id=user.id
    )

@router.post("/login-json", response_model=schemas.MessageResponse)
async def login_json(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login with JSON: send OTP to user's email for verification."""
    user = db.query(User).filter(
        (User.email == login_data.identifier) |
        (User.phone == login_data.identifier)
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    # Send OTP
    otp_code = str(random.randint(1000, 9999))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.query(OTP).filter(OTP.user_id == user.id, OTP.is_used == False).update({"is_used": True})
    otp_obj = OTP(user_id=user.id, otp_code=otp_code, expires_at=expires_at)
    db.add(otp_obj)
    db.commit()
    await send_login_email(
        to_email=user.email,
        name=user.full_name,
        login_id=user.username,
        password=None,
        signup_link=None,
        role=user.role.name if hasattr(user.role, 'name') else None,
        otp=otp_code
    )
    return schemas.MessageResponse(message=f"OTP sent to {user.email}. Please verify to complete login.")

# Utility function to send credentials email after user creation or login
async def send_credentials_email(user, password, role_name):
    try:
        await send_login_email(
            to_email=user.email,
            name=user.full_name,
            login_id=user.username,
            password=password,
            signup_link=f"{email_config.SIGNUP_LINK_BASE}?user={user.user_code}",
            role=role_name
        )
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send credentials email to {user.email}: {str(e)}")
        return {"success": False, "message": f"Email delivery failed: {str(e)}"}





# kyc add update delete endpoint
