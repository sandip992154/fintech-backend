# Authentication related constants
AUTH_ERRORS = {
    "INVALID_CREDENTIALS": "Invalid credentials. Please check your login details.",
    "USER_NOT_FOUND": "User not found. Please check your login details.",
    "INVALID_OTP": "Invalid or expired OTP. Please try again.",
    "INACTIVE_USER": "Your account is inactive. Please contact support.",
    "EXPIRED_TOKEN": "Your session has expired. Please login again.",
    "INVALID_TOKEN": "Invalid authentication token.",
    "MISSING_TOKEN": "Missing authentication token.",
    "EMAIL_EXISTS": "Email already registered.",
    "PHONE_EXISTS": "Phone number already registered.",
    "INVALID_PASSWORD": "Password must be at least 8 characters, include uppercase, lowercase, digit, and special character.",
    "ROLE_NOT_ALLOWED": "This role is not allowed for registration.",
    "SUPERADMIN_SIGNUP": "Super admin signup is not allowed via API. Please contact system administrator."
}

# Token configuration
TOKEN_TYPE = "bearer"
TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OTP configuration
OTP_LENGTH = 4
OTP_EXPIRE_MINUTES = 10

# Role specific constants
ROLE_PREFIX_MAP = {
    "super_admin": "BANDSA",
    "admin": "BANDAD",
    "whitelabel": "BANDWL",
    "mds": "BANDMDS",
    "distributor": "BANDDIS",
    "retailer": "BANDRET",
    "customer": "BANDCUS"
}

ALLOWED_ROLES = ["admin", "whitelabel", "mds", "distributor", "retailer", "customer"]

# Dashboard URLs
DASHBOARD_URLS = {
    "admin": "/admin",
    "whitelabel": "/whitelabel",
    "mds": "/mds",
    "distributor": "/distributor",
    "retailer": "/retailer",
    "customer": "/customer",
    "super_admin": "/superadmin"
}

# Password validation regex
PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\d]).{8,}$'

# Superadmin constants
SUPERADMIN_USER_CODE = "BANDSA00001"