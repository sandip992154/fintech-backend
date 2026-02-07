from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum,func
from sqlalchemy.orm import relationship
from database.database import Base
import enum

class TransactionType(str, enum.Enum):
    RECHARGE = "recharge"
    BILL_PAYMENT = "bill_payment"
    MONEY_TRANSFER = "money_transfer"
    WALLET_TOPUP = "wallet_topup"
    COMMISSION = "commission"
    REFUND = "refund"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class ServiceType(str, enum.Enum):
    MOBILE = "mobile"
    DTH = "dth"
    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    BROADBAND = "broadband"
    LANDLINE = "landline"
    INSURANCE = "insurance"
    CREDIT_CARD = "credit_card"

class ProviderType(str, enum.Enum):
    mobile_recharge = "Mobile Recharge"
    aeps = "AEPS"
    dmt = "DMT"
    dth_recharge = "DTH Recharge"
    micro_atm = "Micro ATM"
    bill_payment = "Bill Payment"

class ChargeType(str, enum.Enum):
    commission = "commission"
    charge = "charge"

class CompanyStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    delete = "delete"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType, name="transaction_type_enum", native_enum=True))
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus, name="transaction_status_enum", native_enum=True), default=TransactionStatus.PENDING)
    reference_id = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    provider_id = Column(Integer, ForeignKey("service_providers.id"))
    
    user = relationship("User", back_populates="transactions")
    provider = relationship("ServiceProvider", back_populates="transactions")

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    balance = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # user = relationship("User", back_populates="wallet")  # Temporarily commented out
    transactions = relationship("WalletTransaction", back_populates="wallet")

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    amount = Column(Float)
    transaction_type = Column(String(50))  # credit/debit
    reference_id = Column(String(100))  # Reference to main transaction if applicable
    balance_after = Column(Float)  # Balance after this transaction
    created_at = Column(DateTime, default=datetime.utcnow)
    
    wallet = relationship("Wallet", back_populates="transactions")

class CommissionStructure(Base):
    __tablename__ = "commission_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    service_id = Column(Integer, ForeignKey("service_providers.id"))
    commission_percentage = Column(Float)
    charge_percentage = Column(Float)
    min_amount = Column(Float, default=0.0)
    max_amount = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    role = relationship("Role", back_populates="commission_structures")
    service = relationship("ServiceProvider", back_populates="commission_structures")

class ServiceCategory(Base):
    __tablename__ = "service_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    description = Column(String(255))
    service_type = Column(Enum(ServiceType))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    providers = relationship("ServiceProvider", back_populates="category")

class ServiceProvider(Base):
    __tablename__ = "service_providers"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(255), nullable=False)
    provider_type = Column(Enum(ProviderType), nullable=False)
    status = Column(Enum(CompanyStatus), default=CompanyStatus.active, nullable=False)
    charge_type = Column(Enum(ChargeType), nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    api_endpoint = Column(String(255))
    api_key = Column(String(255))
    api_secret = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="provider")
    commission_structures = relationship("CommissionStructure", back_populates="service")
    category = relationship("ServiceCategory", back_populates="providers")
    transactions = relationship("Transaction", back_populates="provider")
