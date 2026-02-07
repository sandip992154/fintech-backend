from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base

class UserMPIN(Base):
    __tablename__ = "user_mpins"

    id = Column(Integer, primary_key=True, index=True)
    user_code = Column(String(50), ForeignKey("users.user_code"), unique=True, nullable=False)
    mpin_hash = Column(String(255), nullable=False)  # Store hashed MPIN
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used = Column(DateTime(timezone=True))
    last_reset = Column(DateTime(timezone=True))
    
    # Relationship with User model
    user = relationship("User", back_populates="mpin")

    def __repr__(self):
        return f"<UserMPIN user_code={self.user_code}>"