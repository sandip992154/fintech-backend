"""
Validation utilities for data validation and sanitization
"""
import re
from typing import Optional, Dict, Any
from datetime import datetime, date
import mimetypes

def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate Indian phone number format"""
    # Remove any spaces, dashes, or plus signs
    phone_clean = re.sub(r'[\s\-\+]', '', phone)
    
    # Check if it's a valid Indian mobile number
    # Indian mobile numbers: 10 digits starting with 6-9
    # Or with country code: +91 followed by 10 digits
    patterns = [
        r'^[6-9]\d{9}$',  # 10 digits starting with 6-9
        r'^91[6-9]\d{9}$',  # With country code (91)
    ]
    
    return any(re.match(pattern, phone_clean) for pattern in patterns)

def validate_pan(pan: str) -> bool:
    """Validate PAN number format"""
    # PAN format: 5 letters, 4 digits, 1 letter
    pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return bool(re.match(pan_pattern, pan.upper()))

def validate_aadhaar(aadhaar: str) -> bool:
    """Validate Aadhaar number format"""
    # Remove spaces and check if it's 12 digits
    aadhaar_clean = re.sub(r'\s', '', aadhaar)
    return bool(re.match(r'^\d{12}$', aadhaar_clean))

def validate_pincode(pincode: str) -> bool:
    """Validate Indian pincode format"""
    # Indian pincode: 6 digits
    return bool(re.match(r'^\d{6}$', pincode))

def validate_mpin(mpin: str) -> bool:
    """Validate MPIN format"""
    # MPIN should be 4 or 6 digits
    return bool(re.match(r'^\d{4}$|^\d{6}$', mpin))

def validate_file_type(filename: str, allowed_types: list) -> bool:
    """Validate file type based on extension"""
    if not filename:
        return False
    
    file_extension = filename.lower().split('.')[-1]
    return file_extension in allowed_types

def validate_file_size(file_size: int, max_size_mb: int = 5) -> bool:
    """Validate file size"""
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    return file_size <= max_size_bytes

def sanitize_string(value: str) -> str:
    """Sanitize string input"""
    if not value:
        return ""
    
    # Remove HTML tags and special characters
    clean_value = re.sub(r'<[^>]+>', '', value)  # Remove HTML tags
    clean_value = re.sub(r'[<>"\']', '', clean_value)  # Remove dangerous chars
    return clean_value.strip()

def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """Validate date format"""
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def validate_age(birth_date: str, min_age: int = 18) -> bool:
    """Validate minimum age requirement"""
    try:
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))
        return age >= min_age
    except ValueError:
        return False

def validate_user_code_format(user_code: str) -> bool:
    """Validate user code format"""
    # User code should be alphanumeric and 8-12 characters
    return bool(re.match(r'^[A-Z0-9]{8,12}$', user_code))

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return detailed feedback"""
    result = {
        "is_valid": False,
        "score": 0,
        "feedback": []
    }
    
    if len(password) < 8:
        result["feedback"].append("Password must be at least 8 characters long")
    else:
        result["score"] += 1
    
    if not re.search(r'[A-Z]', password):
        result["feedback"].append("Password must contain at least one uppercase letter")
    else:
        result["score"] += 1
    
    if not re.search(r'[a-z]', password):
        result["feedback"].append("Password must contain at least one lowercase letter")
    else:
        result["score"] += 1
    
    if not re.search(r'\d', password):
        result["feedback"].append("Password must contain at least one number")
    else:
        result["score"] += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["feedback"].append("Password must contain at least one special character")
    else:
        result["score"] += 1
    
    # Password is valid if score is at least 4 out of 5
    result["is_valid"] = result["score"] >= 4
    
    if result["is_valid"]:
        result["feedback"] = ["Password is strong"]
    
    return result

def validate_indian_bank_account(account_number: str) -> bool:
    """Validate Indian bank account number format"""
    # Indian bank account numbers are typically 9-18 digits
    account_clean = re.sub(r'\s', '', account_number)
    return bool(re.match(r'^\d{9,18}$', account_clean))

def validate_ifsc_code(ifsc: str) -> bool:
    """Validate Indian IFSC code format"""
    # IFSC format: 4 letters, 0, 6 alphanumeric characters
    ifsc_pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    return bool(re.match(ifsc_pattern, ifsc.upper()))

def get_mime_type(filename: str) -> Optional[str]:
    """Get MIME type of file"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate GPS coordinates"""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180

def clean_phone_number(phone: str) -> str:
    """Clean and format phone number"""
    # Remove all non-digit characters
    clean_phone = re.sub(r'\D', '', phone)
    
    # If it starts with 91, remove it (Indian country code)
    if clean_phone.startswith('91') and len(clean_phone) == 12:
        clean_phone = clean_phone[2:]
    
    return clean_phone

def validate_business_registration(reg_number: str, reg_type: str) -> bool:
    """Validate business registration number based on type"""
    if reg_type.upper() == "GST":
        # GST format: 15 characters (2 digits + 10 PAN + 1 digit + 1 letter + 1 digit)
        return bool(re.match(r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}$', reg_number.upper()))
    
    elif reg_type.upper() == "CIN":
        # CIN format: 21 characters
        return bool(re.match(r'^[A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$', reg_number.upper()))
    
    elif reg_type.upper() == "LLP":
        # LLP format: 8 characters
        return bool(re.match(r'^[A-Z]{3}-\d{4}$', reg_number.upper()))
    
    return False