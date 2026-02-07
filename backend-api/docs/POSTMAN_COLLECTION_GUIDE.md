# 🚀 Updated Postman Collection - Role-Based Authentication

## ✅ **Collection Successfully Updated!**

The Bandru API Postman collection has been completely enhanced with comprehensive role-based authentication features.

## 📋 **What's New in Version 2.0.0**

### 🔐 **Enhanced Authentication System**
- **Dual Login Methods**: Both OAuth2 form-data and JSON-based login
- **Role-Based Registration**: Register users with specific roles
- **7-Tier Role Hierarchy**: super_admin → admin → whitelabel → mds → distributor → retailer → customer
- **Automatic Token Management**: Test scripts auto-save tokens to environment variables

### 👥 **Pre-configured Role Testing**
- **Ready-to-use examples** for different user roles
- **Super Admin, Customer, Retailer** registration and login examples
- **Role-specific tokens** stored in separate environment variables

### ⚡ **Smart Features**
- **Auto token extraction** from responses
- **Token expiry validation** in pre-request scripts
- **Permission testing endpoints** to verify role-based access control
- **Global error handling** for 401/403 responses

## 🎯 **How to Use the Collection**

### **Step 1: Import the Collection**
1. Open Postman
2. Import `Bandru_API.postman_collection.json`
3. Import `Bandru_API_Local_Environment.postman_environment.json`

### **Step 2: Test Role-Based Authentication**
1. **Register a Super Admin**:
   - Go to "👥 Role Testing Examples" → "Register Super Admin"
   - Click Send (saves token as `super_admin_token`)

2. **Register a Customer**:
   - Go to "👥 Role Testing Examples" → "Register Customer" 
   - Click Send (saves token as `customer_token`)

3. **Test Login Methods**:
   - Try both "Login (Form Data)" and "Login (JSON)" endpoints
   - Observe role and permissions in response

### **Step 3: Test Permission System**
1. **Admin Access**: Use `super_admin_token` to access admin endpoints
2. **Customer Restriction**: Try using `customer_token` on admin endpoints (should get 403)
3. **Role Hierarchy**: Test different roles to see permission differences

## 🔧 **Available Roles & Permissions**

| Role | Level | Typical Permissions |
|------|-------|-------------------|
| `super_admin` | 1 | Full system access |
| `admin` | 2 | User management, reports |
| `whitelabel` | 3 | Partner management |
| `mds` | 4 | Distribution management |
| `distributor` | 5 | Agent management |
| `retailer` | 6 | Customer services |
| `customer` | 7 | Basic transactions |

## 📊 **Collection Sections**

### 🔐 **Role-Based Authentication**
- Register with role
- Dual login methods
- Token refresh
- Get current user
- Available roles

### 👥 **Role Testing Examples**
- Pre-configured user registrations
- Role-specific login examples
- Permission testing scenarios

### 💼 **Business Services**
- Commission structure
- Commission calculation

### 🔧 **Additional Services**
- Service listings
- Service requests

### 📊 **Health & Status**
- API health checks
- Documentation links

## 🌟 **Key Environment Variables**

The collection automatically manages these variables:
- `access_token` - Current user's token
- `refresh_token` - For token renewal
- `user_role` - Current user's role
- `super_admin_token` - Super admin access
- `customer_token` - Customer access
- `retailer_token` - Retailer access

## 🚀 **Ready for Testing!**

Your Bandru API now has a comprehensive Postman collection with:
- ✅ Complete role-based authentication
- ✅ Automated token management
- ✅ Permission testing capabilities
- ✅ Ready-to-use examples for all roles
- ✅ Smart error handling and validation

**Server Status**: ✅ Running on http://localhost:8000

Start testing your role-based authentication system immediately!
