"""
OTP (One-Time Password) Service for PIN management verification.
Handles OTP generation, storage, validation, and cleanup.
"""

# BUG FIX: replaced insecure `random` with `secrets` for cryptographic OTP generation
import secrets
import hmac
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database.database import get_db
from services.models.models import User, OTPRequest
from services.integrations.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

# ── OTP HMAC helpers ──────────────────────────────────────────────────────────
# IMPORTANT: Set OTP_HASH_SECRET in environment variables before deploying.
# A missing secret falls back to a hardcoded value which MUST be changed.
_OTP_HMAC_KEY: bytes = os.getenv(
    "OTP_HASH_SECRET", "bandrupay-otp-secret-CHANGE-IN-PRODUCTION"
).encode("utf-8")


def _hash_otp(plain_otp: str) -> str:
    """
    Hash a plain-text OTP with HMAC-SHA256.
    Stored in DB so the raw OTP is never at rest in plain form.
    Even if the database is dumped, OTPs cannot be reversed without the key.
    """
    return hmac.new(_OTP_HMAC_KEY, plain_otp.encode("utf-8"), hashlib.sha256).hexdigest()


def _verify_otp_hash(plain_otp: str, stored_hash: str) -> bool:
    """
    Constant-time comparison prevents timing-attack enumeration.
    Always call this instead of plain == comparison.
    """
    return hmac.compare_digest(_hash_otp(plain_otp), stored_hash)

class OTPService:
    """Service for managing OTP generation and verification for PIN changes."""
    
    def __init__(self):
        try:
            self.email_service = EmailService()
        except Exception as e:
            logger.error(f"Failed to initialize EmailService: {e}")
            self.email_service = None
        
        self.otp_length = 6
        self.otp_expiry_minutes = 5  # OTP expires after 5 minutes
        
    def generate_otp(self) -> str:
        # BUG FIX: was random.choices (not crypto-safe). secrets.choice is
        # cryptographically random and suitable for security codes.
        return ''.join(secrets.choice('0123456789') for _ in range(self.otp_length))
    
    def create_otp_request(
        self, 
        db: Session, 
        user_id: int, 
        purpose: str = "pin_change"
    ) -> Dict[str, Any]:
        """
        Create a new OTP request for a user.
        
        Args:
            db: Database session
            user_id: User ID requesting OTP
            purpose: Purpose of OTP (pin_change, pin_setup, etc.)
            
        Returns:
            Dict with success status and message
        """
        try:
            # Get user details
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Invalidate any existing OTP for this user and purpose
            existing_otps = db.query(OTPRequest).filter(
                OTPRequest.user_id == user_id,
                OTPRequest.purpose == purpose,
                OTPRequest.is_verified == False,
                OTPRequest.expires_at > datetime.utcnow()
            ).all()
            
            for otp in existing_otps:
                otp.is_expired = True
            
            # Generate new OTP (plain only used for email; DB stores the hash)
            otp_code = self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)

            # BUG FIX: store HMAC hash of OTP, never the plain value.
            # Requires otp_requests.otp_code column to be VARCHAR(64) — see migration note.
            otp_hash = _hash_otp(otp_code)

            # Create OTP request record
            otp_request = OTPRequest(
                user_id=user_id,
                otp_code=otp_hash,          # stored as hash, not plaintext
                purpose=purpose,
                expires_at=expires_at,
                created_at=datetime.utcnow(),
                is_verified=False,
                is_expired=False,
                attempts=0,
                max_attempts=3  # BUG FIX: was 5; requirement is max 3 attempts
            )
            
            db.add(otp_request)
            db.commit()
            db.refresh(otp_request)
            
            # Send OTP via email — rollback if sending fails
            # otp_code (plain) is passed to email; otp_hash is already in the DB
            email_sent = self._send_otp_email(user, otp_code, purpose)
            
            if not email_sent:
                logger.error(f"Failed to send OTP email to user {user_id}; rolling back OTP record")
                db.delete(otp_request)
                db.commit()
                return {
                    "success": False,
                    "message": "Failed to send OTP email. Please check your email configuration or try again later."
                }
            
            return {
                "success": True,
                "message": f"OTP sent successfully to {user.email}. It expires in {self.otp_expiry_minutes} minutes.",
                "otp_id": otp_request.id,
                "expires_at": expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating OTP request: {str(e)}")
            db.rollback()
            return {"success": False, "message": "Failed to generate OTP"}
    
    def verify_otp(
        self, 
        db: Session, 
        user_id: int, 
        otp_code: str, 
        purpose: str = "pin_change"
    ) -> Dict[str, Any]:
        """
        Verify an OTP for a user.
        
        Args:
            db: Database session
            user_id: User ID
            otp_code: OTP code to verify
            purpose: Purpose of OTP verification
            
        Returns:
            Dict with verification result
        """
        try:
            # Find active OTP request
            otp_request = db.query(OTPRequest).filter(
                OTPRequest.user_id == user_id,
                OTPRequest.purpose == purpose,
                OTPRequest.is_verified == False,
                OTPRequest.is_expired == False,
                OTPRequest.expires_at > datetime.utcnow()
            ).first()
            
            if not otp_request:
                return {"success": False, "message": "No valid OTP found or OTP expired"}
            
            # Check attempt limit before doing any comparison
            if otp_request.attempts >= otp_request.max_attempts:
                otp_request.is_expired = True
                db.commit()
                # Generic message: don't reveal why it failed
                return {"success": False, "message": "OTP is no longer valid. Please request a new one."}

            # BUG FIX: was incrementing attempts BEFORE checking the code.
            # This pre-consumed an attempt even on a correct entry.
            # Now we only increment on a wrong guess (correct entry leaves counter unchanged).
            if not _verify_otp_hash(otp_code, otp_request.otp_code):
                otp_request.attempts += 1
                remaining = otp_request.max_attempts - otp_request.attempts
                if otp_request.attempts >= otp_request.max_attempts:
                    otp_request.is_expired = True
                db.commit()
                # Generic message for security; remaining hint is acceptable UX
                return {
                    "success": False,
                    "message": (
                        "Invalid OTP."
                        if remaining <= 0
                        else f"Invalid OTP. {remaining} attempt(s) remaining."
                    ),
                }

            # Correct OTP — mark as verified; do NOT increment attempts
            otp_request.is_verified = True
            otp_request.verified_at = datetime.utcnow()
            db.commit()

            return {"success": True, "message": "OTP verified successfully"}
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            db.rollback()
            return {"success": False, "message": "Failed to verify OTP"}
    
    def cleanup_expired_otps(self, db: Session) -> int:
        """
        Clean up expired OTP requests.
        
        Args:
            db: Database session
            
        Returns:
            Number of cleaned up records
        """
        try:
            expired_otps = db.query(OTPRequest).filter(
                OTPRequest.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_otps)
            
            for otp in expired_otps:
                otp.is_expired = True
            
            db.commit()
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs: {str(e)}")
            return 0
    
    def _send_otp_email(self, user: User, otp_code: str, purpose: str) -> bool:
        """
        Send OTP via email.
        
        Args:
            user: User object
            otp_code: OTP code to send
            purpose: Purpose of OTP
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.email_service:
            logger.error("EmailService not available")
            return False
            
# BUG FIX: removed the line that logged the raw OTP code.
            # Logging sensitive credentials creates audit-trail exposure risk.
            logger.info("Sending OTP email to %s for purpose: %s", user.email, purpose)
            
        try:
            subject = "Your BANDARU PAY Security Code"
            
            purpose_text = {
                "pin_change": "change your PIN",
                "pin_setup": "set up your PIN",
                "profile_update": "update your profile"
            }.get(purpose, "verify your identity")
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #333; text-align: center;">BANDARU PAY Security Code</h2>
                    
                    <p>Hello {user.full_name},</p>
                    
                    <p>You requested to {purpose_text}. Please use the following security code:</p>
                    
                    <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <h1 style="margin: 0; font-size: 36px; letter-spacing: 5px;">{otp_code}</h1>
                    </div>
                    
                    <p><strong>Important:</strong></p>
                    <ul>
                        <li>This code will expire in {self.otp_expiry_minutes} minutes</li>
                        <li>Do not share this code with anyone</li>
                        <li>If you didn't request this code, please ignore this email</li>
                    </ul>
                    
                    <p>Thank you for using BANDARU PAY!</p>
                    
                    <hr style="margin: 30px 0;">
                    <p style="color: #666; font-size: 12px; text-align: center;">
                        This is an automated message. Please do not reply to this email.
                    </p>
                </div>
            </body>
            </html>
            """
            
            result = self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                content=html_content
            )
            
            if result:
                logger.info(f"OTP email sent successfully to {user.email}")
            else:
                logger.error(f"Failed to send OTP email to {user.email}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending OTP email: {str(e)}")
            return False

# Global OTP service instance
otp_service = OTPService()