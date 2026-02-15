from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from enum import Enum

class TransactionType(str, Enum):
    RECHARGE = "recharge"
    BILL_PAYMENT = "bill_payment"
    MONEY_TRANSFER = "money_transfer"
    WALLET_TOPUP = "wallet_topup"
    COMMISSION = "commission"
    REFUND = "refund"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class ServiceType(str, Enum):
    MOBILE = "mobile"
    DTH = "dth"
    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    BROADBAND = "broadband"
    LANDLINE = "landline"
    INSURANCE = "insurance"
    CREDIT_CARD = "credit_card"

# Transaction Schemas
class TransactionBase(BaseModel):
    transaction_type: TransactionType
    amount: Decimal = Field(..., ge=0)
    description: Optional[str] = None

class TransactionCreate(TransactionBase):
    provider_id: int

class TransactionUpdate(BaseModel):
    status: TransactionStatus
    description: Optional[str] = None

class TransactionOut(TransactionBase):
    id: int
    user_id: int
    status: TransactionStatus
    reference_id: str
    created_at: datetime
    updated_at: datetime
    provider_id: int

    class Config:
        from_attributes = True

# Wallet Schemas
class WalletBase(BaseModel):
    balance: Decimal = Field(default=0, ge=0)

class WalletCreate(WalletBase):
    user_id: int

class WalletUpdate(BaseModel):
    balance: Decimal = Field(..., ge=0)
    is_active: Optional[bool] = None

class WalletOut(WalletBase):
    id: int
    user_id: int
    last_updated: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Wallet Topup Request Schema
class WalletTopupRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to topup (must be greater than 0)")
    remark: Optional[str] = Field(None, max_length=500, description="Optional remark for the transaction")

class WalletTransferRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to transfer (must be greater than 0)")
    to_user_id: int = Field(..., gt=0, description="Recipient user ID")
    remark: Optional[str] = Field(None, max_length=500, description="Optional remark for the transfer")

# Wallet Transaction Schemas
class WalletTransactionBase(BaseModel):
    amount: Decimal = Field(..., ge=0)
    transaction_type: str
    reference_id: Optional[str] = None
    remark: Optional[str] = None

class WalletTransactionCreate(WalletTransactionBase):
    wallet_id: int

class WalletTransactionOut(WalletTransactionBase):
    id: int
    balance_after: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

# Commission Structure Schemas
class CommissionStructureBase(BaseModel):
    role_id: int
    service_id: int
    commission_percentage: Decimal = Field(..., ge=0, le=100)
    charge_percentage: Decimal = Field(..., ge=0, le=100)
    min_amount: Decimal = Field(default=0, ge=0)
    max_amount: Optional[Decimal] = Field(None, gt=0)

class CommissionStructureCreate(CommissionStructureBase):
    pass

class CommissionStructureUpdate(BaseModel):
    commission_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    charge_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None

class CommissionStructureOut(CommissionStructureBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Service Category Schemas
class ServiceCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    service_type: ServiceType

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[ServiceType] = None
    is_active: Optional[bool] = None

class ServiceCategoryOut(ServiceCategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Service Provider Schemas
class ServiceProviderBase(BaseModel):
    name: str
    category_id: int
    api_endpoint: str
    is_active: bool = True

class ServiceProviderCreate(ServiceProviderBase):
    api_key: str
    api_secret: str

class ServiceProviderUpdate(BaseModel):
    name: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    is_active: Optional[bool] = None

class ServiceProviderOut(ServiceProviderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        exclude = {"api_key", "api_secret"}
