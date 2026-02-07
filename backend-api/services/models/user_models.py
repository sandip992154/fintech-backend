"""
Enhanced database models for User Management, KYC, and MPIN functionality
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from database.database import Base

# Enums for KYC and MPIN
class KYCStatus(str, enum.Enum):
    NOT_SUBMITTED = "not_submitted"
    PENDING = "pending"
    CONFIRMED = "confirmed"  # Changed from APPROVED to match database
    REJECTED = "rejected"
    HOLD = "hold"  # Added HOLD status from database

class DocumentType(str, enum.Enum):
    PAN_CARD_FRONT = "pan_card_front"
    PAN_CARD_BACK = "pan_card_back"
    AADHAR_FRONT = "aadhar_front"
    AADHAR_BACK = "aadhar_back"
    PHOTO = "photo"
    SIGNATURE = "signature"
    ADDRESS_PROOF = "address_proof"
    BANK_STATEMENT = "bank_statement"

# Enhanced KYC Document Model (expanded to store complete KYC data)
class KYCDocument(Base):
    __tablename__ = "kyc_documents"
    __table_args__ = {'extend_existing': True}

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Personal Information
    full_name = Column(String(100))
    date_of_birth = Column(String(20))
    gender = Column(String(20))
    
    # Contact Information
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pin_code = Column(String(10))
    
    # Business Information (for whitelabel)
    business_name = Column(String(255))
    business_type = Column(String(100))
    business_address = Column(Text)
    company_pan_number = Column(String(10))
    
    # Bank Details
    bank_name = Column(String(255))
    account_number = Column(String(50))
    ifsc_code = Column(String(15))
    account_holder_name = Column(String(255))
    branch_name = Column(String(255))
    
    # Document Information (Required)
    pan_card_no = Column(String(10), nullable=False)
    aadhar_card_no = Column(String(12), nullable=False)
    
    # Document URLs
    profile_photo_url = Column(String(500))
    aadhar_card_url = Column(String(500))
    pan_card_url = Column(String(500))
    company_pan_card_url = Column(String(500))
    signature_url = Column(String(500))
    business_license_url = Column(String(500))
    gst_certificate_url = Column(String(500))
    
    # Status and Timestamps
    status = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="kyc_documents")

# MPIN Model
class MPIN(Base):
    __tablename__ = "mpin"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    user_code = Column(String(20), nullable=False, unique=True, index=True)
    
    # MPIN Details
    mpin_hash = Column(String(255), nullable=False)
    is_set = Column(Boolean, default=False)
    
    # Security
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    last_attempt_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="mpin")

# User Profile Model
class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    user_code = Column(String(20), nullable=False, unique=True, index=True)
    
    # Profile Information
    profile_picture = Column(String(500))  # Cloudinary URL
    bio = Column(Text)
    
    # Business Information (for agents)
    business_name = Column(String(200))
    business_type = Column(String(100))
    business_address = Column(Text)
    business_phone = Column(String(15))
    business_email = Column(String(100))
    
    # Additional Details
    alternate_phone = Column(String(15))
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(15))
    
    # Preferences
    notification_preferences = Column(Text)  # JSON string
    language_preference = Column(String(10), default="en")
    theme_preference = Column(String(10), default="light")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")

# OTP Model for verification
class OTP(Base):
    __tablename__ = "otp_records"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_code = Column(String(20), nullable=False, index=True)
    phone = Column(String(15))
    email = Column(String(100))
    
    # OTP Details
    otp_code = Column(String(6), nullable=False)
    purpose = Column(String(50), nullable=False)  # 'mpin_setup', 'kyc_verification', 'login'
    
    # Status and Expiry
    is_used = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime)