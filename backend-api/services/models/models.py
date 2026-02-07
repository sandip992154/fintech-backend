from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey,
    Index, Enum, func, Table, MetaData
)
from sqlalchemy.orm import relationship
import enum

from database.database import Base
from .transaction_models import Transaction

from sqlalchemy import Text
# ---------- Enum Definition ----------
class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"

class CompanyStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    delete = "delete"

# ---------- Model Base ----------
metadata = MetaData()

# ---------- Role Model ----------

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="role", foreign_keys="[User.role_id]")
    commission_structures = relationship("CommissionStructure", back_populates="role")

# ---------- User Model ----------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_code = Column(String(32), unique=True, index=True, nullable=False)  # Primary user identifier
    username = Column(String(50), unique=True, nullable=True, index=True)  # Optional legacy field
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Profile fields
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    pin_code = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    profile_photo = Column(String(500), nullable=True)  # URL to Cloudinary image
    
     # New fields from form (KYC related but commonly used)
    pan_card_number = Column(String(10), nullable=True)  # PAN Card Number
    aadhaar_card_number = Column(String(12), nullable=True)  # Aadhaar Card Number
    shop_name = Column(String(255), nullable=True)  # Shop Name
    company_name = Column(String(255), nullable=True)  # Company Name
    scheme = Column(String(100), nullable=True)  # Scheme field
    mobile = Column(String(15), nullable=True)  # Mobile field (additional to phone)
    
    # Member Management fields for 7-tier hierarchy
    company_pan_card = Column(String(10), nullable=True)  # Company PAN Card for business roles
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Parent user in hierarchy
    
    # Role relationship
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    role = relationship("Role", back_populates="users")
    tokens = relationship("RefreshToken", back_populates="user")
    bank_accounts = relationship("BankAccount", back_populates="owner")
    kyc_documents = relationship("KYCDocument", back_populates="user", cascade="all, delete-orphan")
    mpin = relationship("MPIN", back_populates="user", uselist=False, cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Member hierarchy relationships
    parent = relationship("User", remote_side=[id], backref="children")
    
    # Transactions
    transactions = relationship("Transaction", back_populates="user", lazy="dynamic")
    # service_transactions = relationship("ServiceTransaction", back_populates="user", lazy="dynamic")  # Temporarily commented out
    
    # Wallet
    # wallet = relationship("Wallet", back_populates="user", uselist=False)  # Temporarily commented out
    
    # Services
    # insurance_policies = relationship("InsurancePolicy", back_populates="user", lazy="dynamic")  # Temporarily commented out
    # pan_applications = relationship("PanCardApplication", back_populates="user", lazy="dynamic")  # Temporarily commented out
    # fastag_vehicles = relationship("FastTagVehicle", back_populates="user", lazy="dynamic")  # Temporarily commented out
    __table_args__ = (Index("ix_users_email_phone", "email", "phone"),)


# ---------- Refresh Token Model ----------

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(Text, unique=True, nullable=False)  # Changed from String(255) to Text
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="tokens")


# ---------- Bank Account Model ----------

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bank_name = Column(String(255))
    ifsc = Column(String(20))
    account_holder = Column(String(255))
    account_number_encrypted = Column(String(1024))
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("User", back_populates="bank_accounts")


# ---------- KYC Document Model ----------
class KYCStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    HOLD = "hold"
    NOT_SUBMITTED = "not_submitted"

# ---------- Company Details Model ----------

class CompanyDetails(Base):
    __tablename__ = "company_details"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    company_fullname = Column(String(255), nullable=True)
    company_logo = Column(String(512), nullable=True)
    company_news = Column(String(1024), nullable=True)
    company_bill_notice = Column(String(1024), nullable=True)
    company_notice_file = Column(String(512), nullable=True)  # store file path or URL
    company_contact_no = Column(String(32), nullable=True)
    company_email = Column(String(255), nullable=True)
    company_website = Column(String(255), nullable=True)
    company_sender_id = Column(String(50), nullable=True)
    company_smsuser = Column(String(255), nullable=True)
    company_smspassword = Column(String(255), nullable=True)
    status = Column(Enum(CompanyStatus), default=CompanyStatus.active, nullable=False)

    added_date = Column(DateTime, server_default=func.now(), nullable=False)
    modified_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

# ---------- OTP Model ----------
class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

# ---------- OTP Request Model ----------
class OTPRequest(Base):
    __tablename__ = "otp_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp_code = Column(String(10), nullable=False)
    purpose = Column(String(50), nullable=False)  # pin_change, pin_setup, profile_update, etc.
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    # Indexes for performance
    __table_args__ = (
        Index('ix_otp_requests_user_purpose', 'user_id', 'purpose'),
        Index('ix_otp_requests_expires_at', 'expires_at'),
        {'extend_existing': True}
    )

    user = relationship("User")