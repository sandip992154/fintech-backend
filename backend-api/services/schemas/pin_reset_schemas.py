"""
Pydantic schemas for the secure PIN reset flow using Email OTP verification.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class SendPinOTPResponse(BaseModel):
    """Response schema for POST /send-pin-otp"""
    message: str
    success: bool = True


class VerifyPinOTPRequest(BaseModel):
    """Request schema for POST /verify-pin-otp"""
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")

    @validator("otp")
    def otp_must_be_numeric(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP must contain digits only")
        return v


class VerifyPinOTPResponse(BaseModel):
    """Response schema for POST /verify-pin-otp"""
    message: str
    success: bool = True


class ResetPinRequest(BaseModel):
    """Request schema for POST /reset-pin"""
    new_pin: str = Field(..., min_length=4, max_length=4, description="New 4-digit numeric PIN")
    confirm_pin: str = Field(..., min_length=4, max_length=4, description="Confirmation of new PIN")

    @validator("new_pin")
    def pin_must_be_numeric(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must contain digits only")
        return v

    @validator("confirm_pin")
    def pins_must_match(cls, v: str, values: dict) -> str:
        if "new_pin" in values and v != values["new_pin"]:
            raise ValueError("new_pin and confirm_pin do not match")
        return v


class ResetPinResponse(BaseModel):
    """Response schema for POST /reset-pin"""
    message: str
    success: bool = True
