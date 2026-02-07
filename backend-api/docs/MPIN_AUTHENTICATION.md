# MPIN Authentication System Documentation

## Overview

The MPIN (Mobile PIN) authentication system provides a secure way for users to access their accounts using a 4-6 digit PIN. This system is designed to work alongside the existing authentication methods and provides a faster way to login for mobile users.

## Features

- MPIN Setup with OTP verification
- Login with MPIN
- MPIN Update with old MPIN and OTP verification
- MPIN Reset with OTP verification
- MPIN Status check

## Technical Details

### Database Structure

The MPIN system uses a dedicated table `user_mpins` with the following structure:

```sql
CREATE TABLE user_mpins (
    id SERIAL PRIMARY KEY,
    user_code VARCHAR(50) UNIQUE NOT NULL REFERENCES users(user_code),
    mpin_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    last_reset TIMESTAMP WITH TIME ZONE
);
```

### API Endpoints

#### 1. Setup MPIN

```http
POST /api/v1/mpin/setup
```

Request:

```json
{
  "identifier": "user@example.com", // email, phone, or user_code
  "mpin": "123456",
  "otp": "123456"
}
```

#### 2. Login with MPIN

```http
POST /api/v1/mpin/login
```

Request:

```json
{
  "identifier": "user@example.com", // email, phone, or user_code
  "mpin": "123456"
}
```

#### 3. Update MPIN

```http
POST /api/v1/mpin/update
```

Request:

```json
{
  "identifier": "user@example.com",
  "old_mpin": "123456",
  "mpin": "654321",
  "otp": "123456"
}
```

#### 4. Reset MPIN

```http
POST /api/v1/mpin/reset
```

Request:

```json
{
  "identifier": "user@example.com",
  "new_mpin": "123456",
  "otp": "123456"
}
```

#### 5. Check MPIN Status

```http
GET /api/v1/mpin/status/{identifier}
```

Response:

```json
{
  "is_set": true,
  "created_at": "2025-09-22T10:00:00Z",
  "last_used": "2025-09-22T11:00:00Z"
}
```

### Security Considerations

1. MPINs are stored as hashed values using bcrypt
2. MPIN setup and reset require OTP verification
3. Failed MPIN attempts are tracked (to be implemented)
4. MPIN updates require both old MPIN and OTP verification
5. All endpoints use HTTPS
6. Rate limiting is applied (to be implemented)

### Integration Guide

1. Include the MPIN router in your FastAPI application:

```python
from services.routers.mpin_router import router as mpin_router
app.include_router(mpin_router)
```

2. Run the alembic migration:

```bash
alembic upgrade head
```

3. Configure OTP settings in your config file.

### Best Practices

1. Use HTTPS for all API calls
2. Implement rate limiting for MPIN attempts
3. Set up monitoring for failed MPIN attempts
4. Regular security audits
5. Implement automatic MPIN reset after multiple failed attempts
