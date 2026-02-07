import pytest
from datetime import datetime, timedelta
import time
from unittest.mock import MagicMock
from services.auth.token_service import TokenService

@pytest.fixture
def mock_redis():
    return MagicMock()

@pytest.fixture
def token_service(mock_redis):
    service = TokenService(mock_redis)
    # Override token expiry for testing
    service.access_token_expires = timedelta(minutes=5)
    service.refresh_token_expires = timedelta(days=1)
    return service

def test_create_access_token(token_service):
    """Test access token creation"""
    data = {"sub": "user123", "role": "admin"}
    token = token_service.create_access_token(data)
    
    # Verify token
    payload = token_service.verify_token(token, verify_type="access")
    assert payload["sub"] == data["sub"]
    assert payload["role"] == data["role"]
    assert payload["type"] == "access"
    assert "exp" in payload

def test_create_refresh_token(token_service):
    """Test refresh token creation"""
    data = {"sub": "user123"}
    token = token_service.create_refresh_token(data)
    
    # Verify token
    payload = token_service.verify_token(token, verify_type="refresh")
    assert payload["sub"] == data["sub"]
    assert payload["type"] == "refresh"
    assert "exp" in payload

def test_blacklist_token(token_service, mock_redis):
    """Test token blacklisting"""
    token = token_service.create_access_token({"sub": "user123"})
    token_service.blacklist_token(token)
    
    # Verify Redis call
    mock_redis.setex.assert_called_once()
    
    # Mock blacklist check
    mock_redis.get.return_value = "revoked"
    assert token_service.is_token_blacklisted(token)

def test_verify_blacklisted_token(token_service, mock_redis):
    """Test verification of blacklisted token"""
    token = token_service.create_access_token({"sub": "user123"})
    
    # Mock token as blacklisted
    mock_redis.get.return_value = "revoked"
    
    with pytest.raises(Exception) as exc_info:
        token_service.verify_token(token)
    assert "revoked" in str(exc_info.value)

def test_token_info_storage(token_service, mock_redis):
    """Test token metadata storage"""
    data = {"sub": "user123"}
    token = token_service.create_access_token(data)
    
    # Mock stored info
    mock_info = {
        "user_id": "user123",
        "type": "access",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + token_service.access_token_expires).isoformat()
    }
    mock_redis.get.return_value = mock_info
    
    # Verify info storage
    assert mock_redis.setex.called
    
    # Mock info retrieval
    token_service.get_token_info(token)
    mock_redis.get.assert_called()

def test_revoke_all_user_tokens(token_service, mock_redis):
    """Test revoking all tokens for a user"""
    user_id = "user123"
    mock_redis.scan_iter.return_value = [b"token:info:token1", b"token:info:token2"]
    mock_redis.get.return_value = '{"user_id": "user123"}'
    
    token_service.revoke_all_user_tokens(user_id)
    
    # Verify blacklist calls
    assert mock_redis.setex.call_count >= 2  # Should be called for each token

def test_verify_token_with_wrong_type(token_service):
    """Test token type verification"""
    token = token_service.create_access_token({"sub": "user123"})
    
    with pytest.raises(Exception) as exc_info:
        token_service.verify_token(token, verify_type="refresh")
    assert "Invalid token type" in str(exc_info.value)

def test_token_expiration(token_service):
    """Test token expiration"""
    # Create token with very short expiration
    token_service.access_token_expires = timedelta(seconds=1)
    token = token_service.create_access_token({"sub": "user123"})
    
    # Wait for token to expire
    time.sleep(2)
    
    with pytest.raises(Exception) as exc_info:
        token_service.verify_token(token)
    assert "expired" in str(exc_info.value)