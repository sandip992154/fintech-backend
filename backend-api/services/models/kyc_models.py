from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime
import enum

class KYCStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    HOLD = "hold"
    NOT_SUBMITTED = "not_submitted"