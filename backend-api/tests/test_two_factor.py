import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pyotp
from passlib.context import CryptContext

from main import app
from services.auth.two_factor import two_factor_auth
from services.models.models import User, TOTPSetup, BackupCode
from database.database import get_db
from tests.conftest import override_get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture
def test_user():
    """Create a test user"""
    return User(
        username="BANDTEST00001",
        email="test@example.com",
        hashed_password=pwd_context.hash("TestPass123!"),
        full_name="Test User",
        phone="1234567890",
        role_id=1,  # We need to specify role_id, not role
        is_active=True
    )

def test_2fa_setup(test_user: User):
    """Test 2FA setup process"""
    db = next(override_get_db())
    
    # Add and persist the user first
    db.add(test_user)
    db.commit()
    
    # Setup 2FA
    setup_response = two_factor_auth.setup_2fa(db, test_user)
    
    # Check response contains required fields
    assert setup_response.secret_key is not None
    assert setup_response.qr_code is not None
    assert len(setup_response.backup_codes) == two_factor_auth.num_backup_codes
    assert setup_response.uri is not None
    assert "otpauth://" in setup_response.uri
    
    # Check database records
    totp_setup = db.query(TOTPSetup).filter(
        TOTPSetup.user_id == test_user.id
    ).first()
    assert totp_setup is not None
    assert totp_setup.secret_key == setup_response.secret_key
    assert not totp_setup.is_enabled  # Should be false until verified
    
    backup_codes = db.query(BackupCode).filter(
        BackupCode.user_id == test_user.id
    ).all()
    assert len(backup_codes) == two_factor_auth.num_backup_codes

def test_totp_verification(test_user: User):
    """Test TOTP verification"""
    db = next(override_get_db())
    
    # Add and persist the user first
    db.add(test_user)
    db.commit()
    
    # Setup 2FA first
    setup_response = two_factor_auth.setup_2fa(db, test_user)
    
    # Generate valid TOTP code right away
    totp = pyotp.TOTP(setup_response.secret_key)
    valid_code = totp.now()
    print(f"Test using code: {valid_code}")
    verification_result = two_factor_auth.verify_totp(db, test_user, valid_code)
    assert verification_result, f"TOTP verification failed with code {valid_code}"
    
    # Refresh database state
    db.refresh(test_user)
    
    # Check that 2FA is now enabled
    totp_setup = db.query(TOTPSetup).filter(
        TOTPSetup.user_id == test_user.id
    ).first()
    assert totp_setup is not None, "TOTP setup not found"
    assert totp_setup.is_enabled, "TOTP was not enabled after verification"
    assert totp_setup.verified_at is not None, "Verified at timestamp not set"
    
    # Test invalid code
    assert not two_factor_auth.verify_totp(db, test_user, "000000"), "Invalid code was accepted"
    
    # Test code reuse (should fail)
    assert not two_factor_auth.verify_totp(db, test_user, valid_code), "Reused code was accepted"

def test_backup_codes(test_user: User):
    """Test backup codes functionality"""
    db = next(override_get_db())
    
    # Add and persist the user first
    db.add(test_user)
    db.commit()
    
    # Setup 2FA first
    setup_response = two_factor_auth.setup_2fa(db, test_user)
    db.commit()  # Ensure setup is committed
    db.refresh(test_user)  # Refresh the user object
    
    # Test valid backup code
    valid_code = setup_response.backup_codes[0]
    assert two_factor_auth.verify_backup_code(db, test_user, valid_code)
    
    # Test that the same code cannot be used again
    assert not two_factor_auth.verify_backup_code(db, test_user, valid_code)
    
    # Test invalid code
    assert not two_factor_auth.verify_backup_code(db, test_user, "invalid_code")
    
    # Check that the code is marked as used in database
    db.refresh(test_user)  # Refresh to ensure we have latest state
    used_code = db.query(BackupCode).filter(
        BackupCode.user_id == test_user.id,
        BackupCode.is_used == True
    ).first()
    assert used_code is not None, "Backup code was not marked as used"
    assert used_code.used_at is not None, "Used at timestamp not set"

def test_disable_2fa(test_user: User):
    """Test 2FA disabling"""
    db = next(override_get_db())
    db.add(test_user)  # Add to current session
    
    # Setup and enable 2FA first
    setup_response = two_factor_auth.setup_2fa(db, test_user)
    db.commit()  # Ensure setup is committed
    db.refresh(test_user)  # Refresh the user object
    
    # Generate valid TOTP code and immediately verify
    totp = pyotp.TOTP(setup_response.secret_key)
    valid_code = totp.now()
    print(f"Disable test using code: {valid_code}")
    assert two_factor_auth.verify_totp(db, test_user, valid_code), "TOTP verification failed"
    db.commit()  # Ensure verification is committed
    db.refresh(test_user)  # Refresh the user object
    
    # Verify 2FA is enabled
    totp_setup = db.query(TOTPSetup).filter(
        TOTPSetup.user_id == test_user.id
    ).first()
    assert totp_setup is not None, "TOTP setup not found"
    assert totp_setup.is_enabled, "2FA was not enabled after verification"
    
    # Disable 2FA
    two_factor_auth.disable_2fa(db, test_user)
    db.commit()  # Ensure disable is committed
    db.refresh(test_user)  # Refresh the user object
    
    # Check that all 2FA data is removed
    totp_setup = db.query(TOTPSetup).filter(
        TOTPSetup.user_id == test_user.id
    ).first()
    assert totp_setup is None, "TOTP setup was not deleted"
    
    backup_codes = db.query(BackupCode).filter(
        BackupCode.user_id == test_user.id
    ).all()
    assert len(backup_codes) == 0, "Backup codes were not deleted"

def test_regenerate_backup_codes(test_user: User):
    """Test backup codes regeneration"""
    db = next(override_get_db())
    db.add(test_user)  # Add to current session
    
    # Setup and enable 2FA first
    setup_response = two_factor_auth.setup_2fa(db, test_user)
    db.commit()  # Ensure setup is committed
    db.refresh(test_user)  # Refresh the user object
    
    # Generate valid TOTP code and immediately verify
    totp = pyotp.TOTP(setup_response.secret_key)
    valid_code = totp.now()
    print(f"Regenerate test using code: {valid_code}")
    assert two_factor_auth.verify_totp(db, test_user, valid_code), "TOTP verification failed"
    db.commit()  # Ensure verification is committed
    db.refresh(test_user)  # Refresh the user object
    
    # Store original backup codes
    original_codes = setup_response.backup_codes
    original_code_count = len(db.query(BackupCode).filter(
        BackupCode.user_id == test_user.id
    ).all())
    
    # Regenerate backup codes
    new_codes = two_factor_auth.regenerate_backup_codes(db, test_user)
    db.commit()  # Ensure regeneration is committed
    db.refresh(test_user)  # Refresh the user object
    
    # Check that we got new codes
    assert len(new_codes) == two_factor_auth.num_backup_codes, "Wrong number of new backup codes"
    assert set(new_codes) != set(original_codes), "New codes are same as original codes"
    
    # Check database
    backup_codes = db.query(BackupCode).filter(
        BackupCode.user_id == test_user.id
    ).all()
    assert len(backup_codes) == two_factor_auth.num_backup_codes, "Wrong number of backup codes in database"
    assert len(backup_codes) == original_code_count, "Backup code count changed unexpectedly"