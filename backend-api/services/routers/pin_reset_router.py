"""
Secure PIN Reset router using Email OTP verification.

Endpoints:
  POST /api/v1/pin/send-otp    — send a 6-digit OTP to the user's registered email
  POST /api/v1/pin/verify-otp  — verify the OTP and mark it as confirmed
  POST /api/v1/pin/reset       — set the new 4-digit PIN after OTP is verified
"""

import random
import logging
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database.database import get_db
from services.auth.auth import get_current_user
from services.models.models import User, OTPRequest
from services.models.user_models import MPIN
from services.schemas.pin_reset_schemas import (
    SendPinOTPResponse,
    VerifyPinOTPRequest,
    VerifyPinOTPResponse,
    ResetPinRequest,
    ResetPinResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pin", tags=["PIN Management"])

# ── bcrypt context for hashing the 4-digit PIN ────────────────────────────────
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── constants ─────────────────────────────────────────────────────────────────
_OTP_PURPOSE = "pin_reset"
_OTP_EXPIRY_MINUTES = 5
_OTP_RATE_LIMIT_COUNT = 3        # max OTP requests …
_OTP_RATE_LIMIT_WINDOW_MINUTES = 10  # … per this many minutes
_MAX_VERIFY_ATTEMPTS = 5         # brute-force guard per OTP record


# ── helpers ───────────────────────────────────────────────────────────────────

def _generate_otp() -> str:
    """Return a cryptographically random 6-digit string."""
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def _hash_pin(plain_pin: str) -> str:
    return _pwd_ctx.hash(plain_pin)


def _send_pin_reset_otp_email(email: str, name: str, otp: str) -> bool:
    """
    Send the PIN-reset OTP e-mail via SMTP.
    Reads credentials from environment variables:
        SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL
    Returns True on success, False on failure (failure is logged but not raised
    so the caller can surface a clean HTTP error).
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", smtp_username)

    if not smtp_username or not smtp_password:
        logger.error("SMTP credentials not configured (SMTP_USERNAME / SMTP_PASSWORD).")
        return False

    subject = "Your PIN Reset OTP – Bandaru Pay"
    body = (
        f"Dear {name},\n\n"
        f"You requested to reset your secure PIN on Bandaru Pay.\n\n"
        f"Your One-Time Password (OTP) is:  {otp}\n\n"
        f"This OTP is valid for {_OTP_EXPIRY_MINUTES} minutes only.\n"
        f"Please do not share this code with anyone.\n\n"
        f"If you did not request a PIN reset, please contact support immediately.\n\n"
        f"Best regards,\n"
        f"Bandaru Pay Security Team"
    )

    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info("PIN reset OTP sent to %s", email)
        return True

    except Exception as exc:
        logger.error("Failed to send PIN reset OTP to %s: %s", email, exc)
        return False


# ── endpoint: POST /api/v1/pin/send-otp ──────────────────────────────────────

@router.post(
    "/send-otp",
    response_model=SendPinOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Send email OTP for PIN reset",
)
def send_pin_otp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SendPinOTPResponse:
    """
    Generate a 6-digit OTP and send it to the authenticated user's registered
    e-mail address.

    Rate limit: at most 3 requests per 10-minute window per user.
    OTP expires after 5 minutes.
    """
    # ── rate-limit check ──────────────────────────────────────────────────────
    window_start = datetime.utcnow() - timedelta(minutes=_OTP_RATE_LIMIT_WINDOW_MINUTES)
    recent_count = (
        db.query(OTPRequest)
        .filter(
            OTPRequest.user_id == current_user.id,
            OTPRequest.purpose == _OTP_PURPOSE,
            OTPRequest.created_at >= window_start,
        )
        .count()
    )
    if recent_count >= _OTP_RATE_LIMIT_COUNT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Too many OTP requests. "
                f"You may request at most {_OTP_RATE_LIMIT_COUNT} OTPs "
                f"every {_OTP_RATE_LIMIT_WINDOW_MINUTES} minutes. "
                f"Please try again later."
            ),
        )

    # ── invalidate all previous unverified OTPs for this user+purpose ─────────
    (
        db.query(OTPRequest)
        .filter(
            OTPRequest.user_id == current_user.id,
            OTPRequest.purpose == _OTP_PURPOSE,
            OTPRequest.is_verified == False,  # noqa: E712
            OTPRequest.is_expired == False,   # noqa: E712
        )
        .update({"is_expired": True})
    )

    # ── generate and persist the new OTP ─────────────────────────────────────
    otp_code = _generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=_OTP_EXPIRY_MINUTES)

    otp_record = OTPRequest(
        user_id=current_user.id,
        otp_code=otp_code,
        purpose=_OTP_PURPOSE,
        expires_at=expires_at,
        created_at=datetime.utcnow(),
        is_verified=False,
        is_expired=False,
        attempts=0,
        max_attempts=_MAX_VERIFY_ATTEMPTS,
    )
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    # ── send the e-mail ───────────────────────────────────────────────────────
    sent = _send_pin_reset_otp_email(
        email=current_user.email,
        name=current_user.full_name,
        otp=otp_code,
    )
    if not sent:
        # Roll back the OTP record so the user can try again
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send OTP email. Please check your email configuration or try again later.",
        )

    return SendPinOTPResponse(
        message=(
            f"OTP sent successfully to {current_user.email}. "
            f"It expires in {_OTP_EXPIRY_MINUTES} minutes."
        )
    )


# ── endpoint: POST /api/v1/pin/verify-otp ─────────────────────────────────────

@router.post(
    "/verify-otp",
    response_model=VerifyPinOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify PIN reset OTP",
)
def verify_pin_otp(
    payload: VerifyPinOTPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerifyPinOTPResponse:
    """
    Validate the OTP previously sent via /send-otp.

    - OTP must belong to the authenticated user.
    - OTP must not be expired.
    - OTP must not already be used/verified.
    - Max {_MAX_VERIFY_ATTEMPTS} wrong guesses are allowed before the record is
      invalidated (brute-force protection).
    """
    # Find the most recent active (not-yet-verified, not-yet-expired) OTP
    otp_record: OTPRequest | None = (
        db.query(OTPRequest)
        .filter(
            OTPRequest.user_id == current_user.id,
            OTPRequest.purpose == _OTP_PURPOSE,
            OTPRequest.is_verified == False,  # noqa: E712
            OTPRequest.is_expired == False,   # noqa: E712
        )
        .order_by(OTPRequest.created_at.desc())
        .first()
    )

    if otp_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP found. Please request a new OTP.",
        )

    # Check wall-clock expiry (belt-and-suspenders alongside the DB flag)
    if otp_record.expires_at < datetime.utcnow():
        otp_record.is_expired = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new OTP.",
        )

    # Brute-force guard: too many wrong attempts
    if otp_record.attempts >= otp_record.max_attempts:
        otp_record.is_expired = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. This OTP has been invalidated. Please request a new one.",
        )

    # Validate the code
    if otp_record.otp_code != payload.otp:
        otp_record.attempts += 1
        remaining = otp_record.max_attempts - otp_record.attempts
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {remaining} attempt(s) remaining.",
        )

    # ── success: mark as verified ─────────────────────────────────────────────
    otp_record.is_verified = True
    otp_record.verified_at = datetime.utcnow()
    db.commit()

    return VerifyPinOTPResponse(message="OTP verified successfully. You may now reset your PIN.")


# ── endpoint: POST /api/v1/pin/reset ─────────────────────────────────────────

@router.post(
    "/reset",
    response_model=ResetPinResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset PIN after OTP verification",
)
def reset_pin(
    payload: ResetPinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResetPinResponse:
    """
    Set a new 4-digit numeric PIN for the authenticated user.

    Pre-conditions:
    - A verified (but not yet consumed) OTP for 'pin_reset' must exist.
    - new_pin == confirm_pin (enforced by Pydantic).
    - PIN must be exactly 4 numeric digits (enforced by Pydantic).

    On success the OTP is invalidated to prevent reuse.
    """
    # ── locate the verified, unconsumed OTP ───────────────────────────────────
    verified_otp: OTPRequest | None = (
        db.query(OTPRequest)
        .filter(
            OTPRequest.user_id == current_user.id,
            OTPRequest.purpose == _OTP_PURPOSE,
            OTPRequest.is_verified == True,   # noqa: E712
            OTPRequest.is_expired == False,   # noqa: E712
        )
        .order_by(OTPRequest.verified_at.desc())
        .first()
    )

    if verified_otp is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not verified. Please complete the OTP verification step before resetting your PIN.",
        )

    # Double-check the OTP is still within its expiry window
    if verified_otp.expires_at < datetime.utcnow():
        verified_otp.is_expired = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Verified OTP has expired. "
                "Please request a new OTP and complete verification again."
            ),
        )

    # ── hash the new PIN ─────────────────────────────────────────────────────
    hashed_pin = _hash_pin(payload.new_pin)

    # ── upsert the MPIN record ────────────────────────────────────────────────
    mpin_record: MPIN | None = (
        db.query(MPIN)
        .filter(MPIN.user_id == current_user.id)
        .first()
    )

    if mpin_record:
        mpin_record.mpin_hash = hashed_pin
        mpin_record.is_set = True
        mpin_record.failed_attempts = 0
        mpin_record.locked_until = None
        mpin_record.updated_at = datetime.utcnow()
    else:
        mpin_record = MPIN(
            user_id=current_user.id,
            user_code=current_user.user_code,
            mpin_hash=hashed_pin,
            is_set=True,
            failed_attempts=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(mpin_record)

    # ── invalidate the OTP so it cannot be reused ────────────────────────────
    verified_otp.is_expired = True
    db.commit()

    logger.info("PIN reset successfully for user_code=%s", current_user.user_code)

    return ResetPinResponse(message="PIN has been reset successfully.")
