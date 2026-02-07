import pyotp
import qrcode
import io
import base64
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import secrets
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from services.models.models import User, TOTPSetup, BackupCode
from services.schemas import schemas
from database.database import get_db

# Password context for hashing backup codes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TwoFactorAuth:
    def __init__(self):
        self.backup_code_length = 8
        self.num_backup_codes = 10
        self.issuer_name = "BandhuruPay"
    
    def _generate_backup_codes(self) -> List[str]:
        """Generate a list of backup codes"""
        codes = []
        while len(codes) < self.num_backup_codes:
            code = secrets.token_hex(self.backup_code_length // 2)
            if code not in codes:  # Ensure uniqueness
                codes.append(code)
        return codes
    
    def _create_qr_code(self, uri: str) -> str:
        """Generate QR code as base64 string"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        
        return f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode()}"
    
    def setup_2fa(self, db: Session, user: User) -> schemas.TOTPSetupResponse:
        """Set up 2FA for a user"""
        # Check if 2FA is already set up
        if user.totp_setup and user.totp_setup.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled for this user"
            )
        
        # Generate new secret key
        secret = pyotp.random_base32()
        
        # Create TOTP URI
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=self.issuer_name
        )
        
        # Generate backup codes
        backup_codes = self._generate_backup_codes()
        
        # Delete any existing TOTP setup
        if user.totp_setup:
            db.delete(user.totp_setup)
            db.query(BackupCode).filter(BackupCode.user_id == user.id).delete()
            db.flush()
        
        # Store TOTP setup
        totp_setup = TOTPSetup(
            user_id=user.id,
            secret_key=secret,
            is_enabled=False  # Will be enabled after verification
        )
        db.add(totp_setup)
        db.flush()  # Get the ID assigned to totp_setup
        
        # Store hashed backup codes
        for code in backup_codes:
            hashed_code = pwd_context.hash(code)
            backup = BackupCode(
                user_id=user.id,
                code=hashed_code
            )
            db.add(backup)
        
        db.commit()
        
        # Generate QR code
        qr_code = self._create_qr_code(uri)
        
        return schemas.TOTPSetupResponse(
            secret_key=secret,
            qr_code=qr_code,
            backup_codes=backup_codes,
            uri=uri
        )
    
    def verify_totp(self, db: Session, user: User, code: str) -> bool:
        """Verify a TOTP code"""
        if not user.totp_setup:
            return False
        
        # Get a fresh transaction
        db.expire_all()
        
        # Refresh the user's TOTP setup from the database
        totp_setup = db.query(TOTPSetup).filter(
            TOTPSetup.user_id == user.id
        ).first()
        
        if not totp_setup:
            return False
        
        # Ensure we don't reuse recently used codes
        if totp_setup.last_code == code:
            current_time = datetime.utcnow()
            last_use_time = totp_setup.last_code_used_at or current_time - timedelta(minutes=1)
            if (current_time - last_use_time).total_seconds() < 30:
                return False
            
        totp = pyotp.TOTP(totp_setup.secret_key)
        
        # Generate time exactly 30 seconds ahead
        future_time = datetime.utcnow() + timedelta(seconds=30)
        
        # Generate verification code at the same time to debug
        expected_code = totp.now()
        print(f"Expected code: {expected_code}, Got code: {code}")
        
        # Verify with a ±1 time step window
        is_valid = totp.verify(code, valid_window=1)
        
        if is_valid:
            if not totp_setup.is_enabled:
                # First successful verification enables 2FA
                totp_setup.is_enabled = True
                totp_setup.verified_at = datetime.utcnow()
            
            # Track the used code
            totp_setup.last_code = code
            totp_setup.last_code_used_at = datetime.utcnow()
            db.add(totp_setup)  # Explicitly mark for update
            db.commit()
            db.refresh(totp_setup)  # Refresh after commit
            return True
        
        return False
    
    def verify_backup_code(self, db: Session, user: User, code: str) -> bool:
        """Verify and consume a backup code"""
        backup_codes = db.query(BackupCode).filter(
            BackupCode.user_id == user.id,
            BackupCode.is_used == False
        ).all()
        
        for backup in backup_codes:
            if pwd_context.verify(code, backup.code):
                backup.is_used = True
                backup.used_at = datetime.utcnow()
                db.commit()
                return True
        
        return False
    
    def disable_2fa(self, db: Session, user: User) -> None:
        """Disable 2FA for a user"""
        if not user.totp_setup or not user.totp_setup.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled for this user"
            )
        
        # Delete TOTP setup
        db.delete(user.totp_setup)
        
        # Delete all backup codes
        db.query(BackupCode).filter(
            BackupCode.user_id == user.id
        ).delete()
        
        db.commit()
    
    def regenerate_backup_codes(
        self,
        db: Session,
        user: User
    ) -> List[str]:
        """Regenerate backup codes for a user"""
        if not user.totp_setup or not user.totp_setup.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA must be enabled to regenerate backup codes"
            )
        
        # Delete existing backup codes
        db.query(BackupCode).filter(
            BackupCode.user_id == user.id
        ).delete()
        
        # Generate and store new backup codes
        new_codes = self._generate_backup_codes()
        for code in new_codes:
            hashed_code = pwd_context.hash(code)
            backup = BackupCode(
                user_id=user.id,
                code=hashed_code
            )
            db.add(backup)
        
        db.commit()
        return new_codes

# Global 2FA manager instance
two_factor_auth = TwoFactorAuth()