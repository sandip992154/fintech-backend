from pydantic import BaseModel, constr
from typing import Optional
from datetime import datetime

class MPINBase(BaseModel):
    mpin: constr(min_length=4, max_length=6, pattern=r'^\d+$')

class MPINSetup(MPINBase):
    identifier: str  # Can be email, phone, or user_code
    otp: str

class MPINLogin(MPINBase):
    identifier: str

class MPINUpdate(MPINBase):
    old_mpin: str
    identifier: str
    otp: str

class MPINReset(BaseModel):
    identifier: str
    otp: str
    new_mpin: constr(min_length=4, max_length=6, pattern=r'^\d+$')

class MPINStatus(BaseModel):
    is_set: bool
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

class MPINResponse(BaseModel):
    message: str
    status: bool

    class Config:
        from_attributes = True