from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database.database import Base

class ServiceType(str, enum.Enum):
    AEPS = "aeps"
    MATM = "matm"
    INSURANCE = "insurance"
    PANCARD = "pancard"
    FASTAG = "fastag"

class ServiceTransaction(Base):
    __tablename__ = "service_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_type = Column(SQLEnum(ServiceType))
    transaction_id = Column(String(50), unique=True, index=True)
    amount = Column(Float)
    status = Column(String(20))  # success, failed, pending
    response_code = Column(String(10))
    response_message = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # user = relationship("User", back_populates="service_transactions")  # Temporarily commented out
    # commission_entries = relationship("CommissionEntry", back_populates="service_transaction")  # Model doesn't exist yet

class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    policy_number = Column(String(50), unique=True, index=True)
    insurance_type = Column(String(50))
    policy_details = Column(String(1000))  # JSON string
    premium_amount = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(20))  # active, expired, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # user = relationship("User", back_populates="insurance_policies")  # Temporarily commented out

class PanCardApplication(Base):
    __tablename__ = "pancard_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    application_number = Column(String(50), unique=True, index=True)
    applicant_details = Column(String(1000))  # JSON string
    status = Column(String(20))  # pending, approved, rejected
    remarks = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # user = relationship("User", back_populates="pan_applications")  # Temporarily commented out

class FastTagVehicle(Base):
    __tablename__ = "fastag_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    vehicle_number = Column(String(20), unique=True, index=True)
    tag_id = Column(String(50), unique=True)
    vehicle_class = Column(String(50))
    status = Column(String(20))  # active, inactive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # user = relationship("User", back_populates="fastag_vehicles")  # Temporarily commented out
    transactions = relationship("FastTagTransaction", back_populates="vehicle")

class FastTagTransaction(Base):
    __tablename__ = "fastag_transactions"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("fastag_vehicles.id"))
    transaction_id = Column(String(50), unique=True, index=True)
    amount = Column(Float)
    type = Column(String(20))  # recharge, toll_deduction
    status = Column(String(20))  # success, failed, pending
    location = Column(String(255))  # For toll deductions
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vehicle = relationship("FastTagVehicle", back_populates="transactions")
