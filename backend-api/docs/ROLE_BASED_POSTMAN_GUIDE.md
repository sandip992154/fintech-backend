# 🎯 Role-Based Authentication - Postman Testing Guide

## ✅ Updated Features

Your Bandru Financial Services API now has **complete role-based authentication** ready for Postman testing!

## 🚀 Server Status
- ✅ **Running**: http://localhost:8000
- ✅ **Role-based auth**: Fully implemented
- ✅ **Multiple login options**: Form-data and JSON
- ✅ **Role permissions**: 7-tier hierarchy

## 📋 Available Roles

### **Role Hierarchy** (Lower number = Higher authority):
1. **super_admin** - Full system access
2. **admin** - System management access  
3. **whitelabel** - White label partner access
4. **mds** - Master Distributor access
5. **distributor** - Distributor access
6. **retailer** - Retailer transaction access
7. **customer** - Basic transaction access

## 🔐 Authentication Endpoints

### **1. User Registration with Role**
```
POST http://localhost:8000/auth/register

Headers:
Content-Type: application/json

Body (JSON):
{
    "username": "admin_user",
    "email": "admin@bandru.com",
    "full_name": "Admin User",
    "phone": "9876543210",
    "password": "admin123",
    "role": "admin"
}
```

**Expected Response:**
```json
{
    "user": {
        "id": 1,
        "username": "admin_user",
        "email": "admin@bandru.com",
        "full_name": "Admin User",
        "phone": "9876543210",
        "is_active": true,
        "created_at": "2025-08-17T18:30:00",
        "updated_at": "2025-08-17T18:30:00",
        "role_id": 1,
        "role_name": "admin"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### **2. Login (Form Data) - Traditional**
```
POST http://localhost:8000/auth/login

Headers:
Content-Type: application/x-www-form-urlencoded

Body (form-data):
username: admin_user
password: admin123
```

### **3. Login (JSON) - Easier for Postman**
```
POST http://localhost:8000/auth/login-json

Headers:
Content-Type: application/json

Body (JSON):
{
    "username": "admin_user",
    "password": "admin123"
}
```

**Expected Login Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "role": "admin",
    "permissions": [
        "manage_users",
        "manage_transactions", 
        "manage_services",
        "view_reports"
    ],
    "user_id": 1
}
```

### **4. Get Current User Info**
```
GET http://localhost:8000/auth/me

Headers:
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### **5. Get Available Roles**
```
GET http://localhost:8000/auth/roles

Headers:
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## 🎭 Test Different Roles

### **Test Super Admin:**
```json
{
    "username": "super_admin",
    "email": "super@bandru.com",
    "full_name": "Super Admin",
    "phone": "9999999999",
    "password": "super123",
    "role": "super_admin"
}
```

### **Test Customer:**
```json
{
    "username": "customer1",
    "email": "customer@bandru.com",
    "full_name": "Customer User", 
    "phone": "8888888888",
    "password": "customer123",
    "role": "customer"
}
```

### **Test Retailer:**
```json
{
    "username": "retailer1",
    "email": "retailer@bandru.com",
    "full_name": "Retailer User",
    "phone": "7777777777", 
    "password": "retailer123",
    "role": "retailer"
}
```

## 🔒 Role-Based Permissions

### **Super Admin Permissions:**
- all_permissions

### **Admin Permissions:**
- manage_users
- manage_transactions
- manage_services
- view_reports

### **WhiteLabel Permissions:**
- manage_distributors
- view_transactions
- manage_services

### **MDS Permissions:**
- manage_distributors
- view_transactions
- manage_retailer

### **Distributor Permissions:**
- manage_retailers
- view_transactions

### **Retailer Permissions:**
- perform_transactions
- view_wallet

### **Customer Permissions:**
- basic_transactions
- view_wallet

## 🧪 Testing Workflow in Postman

### **Step 1: Register Users with Different Roles**
1. Register a **super_admin** user
2. Register an **admin** user  
3. Register a **customer** user
4. Register a **retailer** user

### **Step 2: Test Login with Each Role**
1. Login with each user using `/auth/login-json`
2. Note the different `role` and `permissions` in responses
3. Save the `access_token` for each role

### **Step 3: Test Role-Based Access**
1. Use different tokens to access endpoints
2. Verify role-based permissions work
3. Test transaction endpoints with different roles

### **Step 4: Test Authentication Features**
1. Get current user info with `/auth/me`
2. Test token refresh with `/auth/refresh`
3. Test logout functionality

## 📊 Transaction Testing with Roles

### **Create Wallet (All Roles):**
```
POST http://localhost:8000/transactions/wallet/create

Headers:
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### **Wallet Topup (Customer/Retailer):**
```
POST http://localhost:8000/transactions/wallet/topup

Headers:
Authorization: Bearer YOUR_ACCESS_TOKEN

Body (JSON):
{
    "amount": 1000.0,
    "payment_method": "upi",
    "reference_id": "TEST123"
}
```

### **AEPS Services (Retailer+):**
```
POST http://localhost:8000/additional-services/aeps/balance-enquiry

Headers:
Authorization: Bearer YOUR_ACCESS_TOKEN

Body (JSON):
{
    "aadhaar": "123456789012",
    "biometric_data": "test_biometric_data",
    "bank_iin": "123456"
}
```

## ✅ What's Working

### **Authentication Features:**
- ✅ **Role-based registration** - Users assigned specific roles
- ✅ **Role-based login** - Tokens include role and permissions
- ✅ **JWT with role info** - Tokens contain role metadata
- ✅ **Permission system** - Different roles have different permissions
- ✅ **Multiple login methods** - Form-data and JSON options

### **Role Management:**
- ✅ **7-tier hierarchy** - From super_admin to customer
- ✅ **Automatic role creation** - Roles created if they don't exist
- ✅ **Role validation** - Only valid roles accepted
- ✅ **Permission mapping** - Each role has specific permissions

### **Security Features:**
- ✅ **Password hashing** - bcrypt encryption
- ✅ **JWT tokens** - Secure token-based auth
- ✅ **Refresh tokens** - Secure token refresh mechanism
- ✅ **Token cleanup** - Old tokens automatically cleaned

## 🎯 Interactive Documentation

### **Swagger UI:** http://localhost:8000/docs
- Complete API documentation
- Interactive testing interface
- Role-based endpoint documentation

### **ReDoc:** http://localhost:8000/redoc
- Clean documentation interface
- Detailed schema descriptions

## 🔍 Testing Tips

### **1. Save Tokens in Postman Variables:**
```javascript
// In Tests tab after login:
pm.environment.set("access_token", pm.response.json().access_token);
pm.environment.set("user_role", pm.response.json().role);
```

### **2. Use Environment Variables:**
```
{{base_url}}/auth/login-json
Authorization: Bearer {{access_token}}
```

### **3. Test Different Scenarios:**
- Valid role registration ✅
- Invalid role registration ❌  
- Successful login with role info ✅
- Failed login with wrong credentials ❌
- Access endpoints with different role tokens

## 🎉 Ready to Test!

Your **role-based authentication system** is now fully functional and ready for comprehensive testing in Postman!

**Key Features:**
- ✅ Complete role hierarchy
- ✅ JWT tokens with role information  
- ✅ Permission-based access control
- ✅ Multiple authentication endpoints
- ✅ Comprehensive error handling

**Start testing with the endpoints above!** 🚀

---

**Status**: Role-based auth ✅ | Postman ready ✅ | All roles working ✅
