# KYC Status Configuration
KYC_STATUS = {
    "PENDING": "pending",
    "SUBMITTED": "submitted", 
    "UNDER_REVIEW": "under_review",
    "APPROVED": "approved",
    "REJECTED": "rejected"
}

# MPIN Configuration  
MPIN_CONFIG = {
    "LENGTH": 4,
    "MIN_LENGTH": 4,
    "MAX_LENGTH": 6,
    "MAX_ATTEMPTS": 3,
    "LOCKOUT_DURATION_MINUTES": 30
}

# File Upload Configuration
FILE_UPLOAD_CONFIG = {
    "MAX_SIZE_MB": 5,
    "ALLOWED_EXTENSIONS": ["jpg", "jpeg", "png", "pdf"]
}

# Role Hierarchy Configuration
ROLE_HIERARCHY = {
    "super_admin": {
        "level": 0,
        "description": "Super Administrator with full system access",
        "can_create": ["admin", "whitelabel", "mds", "distributor", "retailer", "customer"]
    },
    "admin": {
        "level": 1,
        "description": "Administrator with system management access",
        "can_create": ["whitelabel", "mds", "distributor", "retailer", "customer"]
    },
    "whitelabel": {
        "level": 2,
        "description": "White label partner with business management access",
        "can_create": ["mds", "distributor", "retailer", "customer"]
    },
    "mds": {
        "level": 3,
        "description": "Master Distributor with network management access",
        "can_create": ["distributor", "retailer", "customer"]
    },
    "distributor": {
        "level": 4,
        "description": "Distributor with regional management access", 
        "can_create": ["retailer", "customer"]
    },
    "retailer": {
        "level": 5,
        "description": "Retailer with service provision access",
        "can_create": ["customer"]
    },
    "customer": {
        "level": 6,
        "description": "End customer with service consumption access",
        "can_create": []
    }
}

# Role Prefix Mapping
ROLE_PREFIX_MAP = {
    "super_admin": "BANDSUP",
    "admin": "BANDADM", 
    "whitelabel": "BANDWHT",
    "mds": "BANDMDS",
    "distributor": "BANDDST",
    "retailer": "BANDRET",
    "customer": "BANDCUS"
}

# Validation Patterns
VALIDATION_PATTERNS = {
    "EMAIL": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "PHONE": r"^[6-9]\d{9}$",
    "PAN": r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
    "PAN_CARD": r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
    "AADHAR": r"^[0-9]{12}$",
    "AADHAR_CARD": r"^[0-9]{12}$",
    "PINCODE": r"^[0-9]{6}$"
}

# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 3
OTP_COOLDOWN_MINUTES = 15

# Valid Permissions for Role-based Access Control
VALID_PERMISSIONS = [
    "schemes.read",
    "schemes.create", 
    "schemes.update",
    "schemes.delete",
    "service_operators.read",
    "service_operators.create",
    "service_operators.update", 
    "service_operators.delete",
    "commissions.read",
    "commissions.create",
    "commissions.update",
    "commissions.delete",
    "commission_slabs.read",
    "commission_slabs.create",
    "commission_slabs.update",
    "commission_slabs.delete",
    "users.read",
    "users.create",
    "users.update",
    "users.delete",
    "reports.read",
    "reports.export"
]
