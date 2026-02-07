# API Reference Guide

## 🔗 Base URL
```
Local Development: http://localhost:8000
Production: https://api.bandarupay.com
```

## 🔐 Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## 📋 Role-Based Access Control

### Role Hierarchy (1 = Highest, 7 = Lowest)
1. **super_admin** - Full system access
2. **admin** - Administrative privileges
3. **whitelabel** - White-label partner access
4. **mds** - Master Distributor access
5. **distributor** - Distributor access
6. **retailer** - Retailer access
7. **customer** - End customer access

### Permission Inheritance
Higher-level roles inherit permissions from lower-level roles.

---

## 🔑 Authentication Endpoints

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "full_name": "string",
  "role": "customer"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "role": "customer",
  "permissions": ["read:profile"],
  "user_id": 1
}
```

### Login User
```http
POST /auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "role": "customer",
  "permissions": ["read:profile"],
  "user_id": 1
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "string"
}
```

### Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "full_name": "string",
  "role": "customer",
  "is_active": true,
  "created_at": "2025-08-17T00:00:00Z"
}
```

---

## 👥 User Management

### List Users (Admin Only)
```http
GET /users/
Authorization: Bearer <admin-token>
```

### Get User by ID
```http
GET /users/{user_id}
Authorization: Bearer <token>
```

### Update User
```http
PUT /users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "string",
  "email": "user@example.com"
}
```

### Delete User (Admin Only)
```http
DELETE /users/{user_id}
Authorization: Bearer <admin-token>
```

---

## 💰 Transaction Endpoints

### Create Wallet
```http
POST /transactions/wallet/create
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "balance": 0.0,
  "created_at": "2025-08-17T00:00:00Z"
}
```

### Wallet Top-up
```http
POST /transactions/wallet/topup
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 1000.0,
  "payment_method": "card"
}
```

### Money Transfer
```http
POST /transactions/transfer
Authorization: Bearer <token>
Content-Type: application/json

{
  "recipient_id": 2,
  "amount": 500.0,
  "description": "Payment for services"
}
```

### Get Wallet Balance
```http
GET /transactions/wallet/balance
Authorization: Bearer <token>
```

**Response:**
```json
{
  "balance": 1500.0,
  "currency": "INR"
}
```

### Transaction History
```http
GET /transactions/history?page=1&limit=10
Authorization: Bearer <token>
```

**Response:**
```json
{
  "transactions": [
    {
      "id": 1,
      "type": "transfer",
      "amount": 500.0,
      "description": "Payment for services",
      "created_at": "2025-08-17T00:00:00Z",
      "status": "completed"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

---

## 🏦 Financial Services

### AEPS Balance Inquiry
```http
POST /additional-services/aeps/balance
Authorization: Bearer <token>
Content-Type: application/json

{
  "mobile_number": "9876543210",
  "aadhar_number": "123456789012",
  "bank_iin": "607152"
}
```

### AEPS Cash Withdrawal
```http
POST /additional-services/aeps/withdrawal
Authorization: Bearer <token>
Content-Type: application/json

{
  "mobile_number": "9876543210",
  "aadhar_number": "123456789012",
  "bank_iin": "607152",
  "amount": 1000.0
}
```

### mATM Initialize
```http
POST /additional-services/matm/initialize
Authorization: Bearer <token>
Content-Type: application/json

{
  "mobile_number": "9876543210",
  "location": "Store Location"
}
```

### mATM Transaction
```http
POST /additional-services/matm/transaction
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "string",
  "transaction_type": "withdrawal",
  "amount": 1000.0
}
```

### Insurance Quotes
```http
POST /additional-services/insurance/quotes
Authorization: Bearer <token>
Content-Type: application/json

{
  "insurance_type": "vehicle",
  "vehicle_number": "MH12AB1234",
  "coverage_amount": 500000.0
}
```

### PAN Card Application
```http
POST /additional-services/pan/apply
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "John Doe",
  "father_name": "Jane Doe",
  "date_of_birth": "1990-01-01",
  "mobile_number": "9876543210",
  "email": "john@example.com",
  "address": "Complete Address"
}
```

### FASTag Recharge
```http
POST /additional-services/fastag/recharge
Authorization: Bearer <token>
Content-Type: application/json

{
  "vehicle_number": "MH12AB1234",
  "amount": 500.0,
  "mobile_number": "9876543210"
}
```

---

## 🛠️ Admin Endpoints

### Role Management

#### List All Roles
```http
GET /auth/roles
Authorization: Bearer <admin-token>
```

#### Create Role
```http
POST /auth/roles
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "name": "new_role",
  "description": "Role description",
  "level": 8
}
```

#### Update Role
```http
PUT /auth/roles/{role_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "description": "Updated description"
}
```

#### Delete Role
```http
DELETE /auth/roles/{role_id}
Authorization: Bearer <admin-token>
```

### User Role Assignment

#### Assign Role to User
```http
POST /auth/users/{user_id}/roles
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "role_name": "retailer"
}
```

#### Remove Role from User
```http
DELETE /auth/users/{user_id}/roles/{role_name}
Authorization: Bearer <admin-token>
```

---

## 📊 System Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-17T00:00:00Z",
  "version": "1.0.0"
}
```

### API Documentation
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

---

## ❌ Error Responses

### Standard Error Format
```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-08-17T00:00:00Z"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Authentication Errors
```json
{
  "detail": "Could not validate credentials",
  "error_code": "INVALID_TOKEN"
}
```

### Permission Errors
```json
{
  "detail": "Insufficient permissions",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🔧 Rate Limiting

Default rate limits:
- **Authentication endpoints**: 5 requests per minute
- **Transaction endpoints**: 10 requests per minute
- **General endpoints**: 100 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1629123456
```

---

## 💡 Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** (httpOnly cookies recommended)
3. **Implement token refresh** logic
4. **Handle errors gracefully**
5. **Use appropriate HTTP methods**
6. **Follow REST conventions**
7. **Validate all inputs**
8. **Use pagination** for large datasets

---

## 📞 Support

For API support:
- **Email**: api-support@bandarupay.com
- **Documentation**: Real-time docs at `/docs`
- **Status Page**: https://status.bandarupay.com
