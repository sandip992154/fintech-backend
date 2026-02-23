"""
Secure PIN Reset router using Email OTP verification.

Endpoints:
  POST /api/v1/pin/send-otp    — send a 6-digit OTP to the user's registered email
  POST /api/v1/pin/verify-otp  — verify the OTP and mark it as confirmed
  POST /api/v1/pin/reset       — set the new 4-digit PIN after OTP is verified
"""

# BUG FIX: replaced `import random` with `secrets` for cryptographically
# random OTP generation. Also added hmac/hashlib for OTP hashing.
import secrets
import hmac
import hashlib
import logging
import os
from datetime import datetime, timedelta

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
from services.integrations.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pin", tags=["PIN Management"])

# ── bcrypt context for hashing the 4-digit PIN ────────────────────────────────
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── constants ─────────────────────────────────────────────────────────────────
_OTP_PURPOSE = "pin_reset"
_OTP_EXPIRY_MINUTES = 5
_OTP_RATE_LIMIT_COUNT = 3        # max OTP requests …
_OTP_RATE_LIMIT_WINDOW_MINUTES = 10  # … per this many minutes
# BUG FIX: was 5; requirement specifies max 3 attempts before lockout
_MAX_VERIFY_ATTEMPTS = 3


# ── OTP HMAC helpers ────────────────────────────────────────────────────────────
# IMPORTANT: set OTP_HASH_SECRET in environment variables before deploying.
_OTP_HMAC_KEY: bytes = os.getenv(
    "OTP_HASH_SECRET", "bandrupay-otp-secret-CHANGE-IN-PRODUCTION"
).encode("utf-8")


def _hash_otp(plain_otp: str) -> str:
    """
    Hash a plain-text OTP with HMAC-SHA256 and a server secret.
    Stored in the DB so the raw OTP is never at rest in plain form.
    Even a full DB dump cannot reverse OTPs without the server key.
    Requires otp_requests.otp_code to be VARCHAR(64) — run the migration script.
    """
    return hmac.new(_OTP_HMAC_KEY, plain_otp.encode("utf-8"), hashlib.sha256).hexdigest()


def _verify_otp_hash(plain_otp: str, stored_hash: str) -> bool:
    """
    Constant-time comparison via hmac.compare_digest.
    Prevents timing-attack enumeration of valid OTP values.
    """
    return hmac.compare_digest(_hash_otp(plain_otp), stored_hash)


# ── helpers ───────────────────────────────────────────────────────────────────

def _generate_otp() -> str:
    # BUG FIX: was random.SystemRandom().randint — while technically
    # using OS entropy, the idiomatic and future-proof way is secrets.randbelow.
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_pin(plain_pin: str) -> str:
    return _pwd_ctx.hash(plain_pin)


def _send_pin_reset_otp_email(email: str, name: str, otp: str) -> bool:
    """
    Send the PIN-reset OTP via the shared EmailService (HTML email).
    """
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
        <div style="background: #f8f9fa; padding: 30px; border-radius: 10px;">
            <h2 style="color: #333; text-align: center; margin-bottom: 4px;">BandruPay</h2>
            <p style="text-align:center; color:#666; margin-top:0;">Secure PIN Reset</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">

            <p>Dear <strong>{name}</strong>,</p>
            <p>You requested to reset your secure PIN. Use the OTP below:</p>

            <div style="background:#4f46e5; color:#fff; padding:20px; border-radius:8px;
                        text-align:center; margin:24px 0; letter-spacing:8px;">
                <span style="font-size:36px; font-weight:bold;">{otp}</span>
            </div>

            <ul style="color:#555; font-size:14px;">
                <li>Valid for <strong>{_OTP_EXPIRY_MINUTES} minutes</strong> only</li>
                <li>Do <strong>not</strong> share this code with anyone</li>
                <li>If you did not request this, contact support immediately</li>
            </ul>

            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color:#999; font-size:12px; text-align:center;">
                This is an automated message &mdash; please do not reply.
            </p>
        </div>
    </body>
    </html>
    """
    try:
        svc = EmailService()
        return svc.send_email(
            to_email=email,
            subject="Your PIN Reset OTP – BandruPay",
            content=html_body,
        )
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

    # Generate OTP plaintext (for email) then hash it for DB storage.
    otp_code = _generate_otp()
    otp_hash = _hash_otp(otp_code)     # BUG FIX: DB stores hash, NOT the plain OTP
    expires_at = datetime.utcnow() + timedelta(minutes=_OTP_EXPIRY_MINUTES)

    otp_record = OTPRequest(
        user_id=current_user.id,
        otp_code=otp_hash,          # stored as HMAC-SHA256 hash
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

    # ── send the e-mail (with the PLAIN otp_code, not the hash) ─────────────────
    sent = _send_pin_reset_otp_email(
        email=current_user.email,
        name=current_user.full_name,
        otp=otp_code,   # plain OTP is only ever sent via email, never stored
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
            # Generic message: don't reveal the lockout threshold
            detail="OTP is no longer valid. Please request a new one.",
        )

    # BUG FIX: was comparing plain-text strings (no hashing, timing-attack risk).
    # Now uses _verify_otp_hash which:
    #   (a) hashes the submitted value before comparing,
    #   (b) uses hmac.compare_digest for constant-time equality.
    if not _verify_otp_hash(payload.otp, otp_record.otp_code):
        otp_record.attempts += 1
        remaining = otp_record.max_attempts - otp_record.attempts
        if otp_record.attempts >= otp_record.max_attempts:
            otp_record.is_expired = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "OTP is no longer valid. Please request a new one."
                if remaining <= 0
                else f"Invalid OTP. {remaining} attempt(s) remaining."
            ),
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

    # ── reject if new PIN is the same as the current PIN ─────────────────────
    if mpin_record and mpin_record.is_set:
        if _pwd_ctx.verify(payload.new_pin, mpin_record.mpin_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New PIN must be different from your current PIN.",
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
