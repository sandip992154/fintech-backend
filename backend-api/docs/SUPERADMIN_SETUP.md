# Superadmin Setup Guide

## 🎯 Overview

The Bandaru Pay backend API now has a robust superadmin initialization system that automatically creates and manages the superadmin user based on credentials specified in the `.env` file.

## ✅ Current Status

**SUPERADMIN USER SUCCESSFULLY CREATED AND CONFIGURED**

### 📋 Superadmin Details

- **User ID**: 1
- **User Code**: `BANDSA000001`
- **Username**: `superadmin`
- **Email**: `rohanchougule090@gmail.com`
- **Phone**: `+919999999999`
- **Full Name**: `Super Admin`
- **Role**: `super_admin`
- **Status**: `Active`
- **Password**: `SuperAdmin@123`

## 🔐 Login Credentials

You can login to the system using any of these credentials:

### Option 1: Email Login

- **Email**: `rohanchougule090@gmail.com`
- **Password**: `SuperAdmin@123`

### Option 2: User Code Login

- **User Code**: `BANDSA000001`
- **Password**: `SuperAdmin@123`

### Option 3: Username Login

- **Username**: `superadmin`
- **Password**: `SuperAdmin@123`

## 🛠️ Configuration (.env file)

The superadmin is configured through these environment variables in your `.env` file:

```env
# =================================
# SUPERADMIN CONFIGURATION
# =================================
SUPERADMIN_USER_CODE=BANDSA000001
SUPERADMIN_USERNAME=superadmin
SUPERADMIN_EMAIL=rohanchougule090@gmail.com
SUPERADMIN_PHONE=+919999999999
SUPERADMIN_PASSWORD=SuperAdmin@123
SUPERADMIN_NAME=Super Admin
```

## 🚀 Automatic Initialization

The superadmin user is automatically created/updated when the server starts:

1. **Server Startup**: When you run the FastAPI server, the `startup_event()` function executes
2. **Role Creation**: The system ensures a `super_admin` role exists
3. **User Management**: The system checks for existing users and creates/updates the superadmin accordingly
4. **Smart Handling**: If a user with the target email already exists, it's updated to be the superadmin
5. **Password Updates**: Existing superadmin passwords are updated to match the .env configuration

## 🔧 Manual Management Scripts

### Primary Script: `scripts/manage_superadmin.py`

This comprehensive script can:

- Check existing superadmin users
- Create new superadmin if none exists
- Update existing users to be superadmin
- Handle email conflicts intelligently
- Display final credentials

**Usage**:

```bash
cd backend-api
python scripts/manage_superadmin.py
```

### Basic Script: `scripts/init_superadmin.py`

A simpler script that directly calls the initialization function.

**Usage**:

```bash
cd backend-api
python scripts/init_superadmin.py
```

## 📁 Implementation Files

### Core Files

1. **`database/init_db.py`**: Contains the `init_superadmin()` function
2. **`main.py`**: Calls superadmin initialization on startup
3. **`config/config.py`**: Reads superadmin settings from .env
4. **`.env`**: Contains superadmin configuration

### Management Scripts

1. **`scripts/manage_superadmin.py`**: Comprehensive user management
2. **`scripts/init_superadmin.py`**: Basic initialization script

## 🔄 How It Works

### Startup Sequence

1. FastAPI app starts
2. `startup_event()` is triggered
3. Database session is created
4. `init_superadmin(db)` is called
5. System checks for existing users
6. Creates/updates superadmin as needed
7. Logs success/failure

### Smart User Handling

The system handles multiple scenarios:

1. **No superadmin exists**: Creates new user
2. **User with target user_code exists**: Updates password and role
3. **User with target email exists**: Updates to use desired user_code
4. **Multiple super_admin role users**: Manages conflicts intelligently

## 🛡️ Security Features

### Password Security

- Passwords are hashed using bcrypt
- Strong default password with mixed case, numbers, and symbols
- Password is updated from .env on every startup

### Role-Based Access

- Dedicated `super_admin` role with full system access
- Role is automatically assigned during user creation/update
- Role hierarchy system for permission management

### Database Safety

- All operations use database transactions
- Automatic rollback on errors
- Comprehensive error logging

## 🧪 Testing & Verification

### Verify Superadmin Creation

```bash
# Run the management script to see current status
python scripts/manage_superadmin.py
```

### Test Login

1. Start the FastAPI server
2. Navigate to the login endpoint
3. Use any of the provided credential combinations
4. Verify you receive admin-level access

### Check Database

```sql
SELECT id, user_code, username, email, full_name, is_active, role_id
FROM users
WHERE user_code = 'BANDSA000001';
```

## 🔧 Troubleshooting

### Common Issues

1. **"Email already exists" error**:

   - Use `scripts/manage_superadmin.py` instead of basic initialization
   - The management script handles email conflicts automatically

2. **Role not found**:

   - The system automatically creates the `super_admin` role
   - Check database for role table integrity

3. **Password not working**:

   - Verify the password in .env matches your attempts
   - Check for extra spaces or special characters
   - Password is case-sensitive: `SuperAdmin@123`

4. **User_code conflicts**:
   - The system updates existing users to use the desired user_code
   - Old user_codes are replaced with the new configuration

### Log Checking

Check the application logs for detailed information:

- Superadmin creation/update messages
- Error details if something fails
- Database operation status

## 📝 Customization

### Changing Superadmin Credentials

1. Update the values in `.env` file
2. Restart the server (automatic update)
3. Or run `python scripts/manage_superadmin.py` manually

### Adding Multiple Superadmins

The current system creates one primary superadmin. To add more:

1. Create additional users through the API
2. Assign them the `super_admin` role
3. Or modify the initialization script to create multiple users

## ✅ Success Confirmation

- ✅ Superadmin user exists in database
- ✅ Correct user_code: `BANDSA000001`
- ✅ Correct email: `rohanchougule090@gmail.com`
- ✅ Password is properly hashed and stored
- ✅ `super_admin` role is assigned
- ✅ User is active and ready for login
- ✅ Automatic initialization on server startup works
- ✅ Manual management scripts are available

## 🎉 Ready to Use!

Your superadmin user is now properly configured and ready for use. You can login using the credentials above and start managing your Bandaru Pay system with full administrative privileges.

---

**Last Updated**: September 23, 2025  
**Status**: ✅ COMPLETED AND VERIFIED  
**Next Steps**: Use the login credentials to access the admin interface
