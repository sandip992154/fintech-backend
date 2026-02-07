# Member Management API Endpoints - Comprehensive Documentation

## Overview

The Member Management system is built using a **two-layer architecture** to handle different levels of functionality:

1. **Core Member Routes** (`/api/v1/members/*`) - Essential CRUD operations and basic member management
2. **Admin Member Routes** (`/api/v1/members/admin/*`) - Advanced administrative features, bulk operations, and enhanced reporting

This separation ensures clean code organization, proper role-based access control, and scalable feature development.

---

## 🔧 Core Member Routes (`member_core_routes.py`)

These endpoints handle the fundamental member management operations that most users need.

### **POST /api/v1/members/create**

**Purpose**: Create a new member in the system  
**Use Case**: When admins need to onboard new team members, agents, or customers  
**Why Created**: Core functionality for user registration and hierarchy building

**Business Logic**:

- Validates role-based permissions (users can only create members in their allowed hierarchy)
- Automatically assigns parent-child relationships based on role hierarchy
- Generates unique user codes and handles email notifications
- Enforces role constraints (e.g., only SuperAdmin can create Admins)

**Request Body**:

```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "9876543210",
  "role_name": "Agent",
  "parent_id": 123,
  "state": "Karnataka",
  "city": "Bangalore",
  "password": "SecurePass123"
}
```

**Response**:

```json
{
  "success": true,
  "member": {
    "id": 456,
    "user_code": "USR456",
    "full_name": "John Doe",
    "email": "john@example.com",
    "role_name": "Agent",
    "is_active": true
  },
  "message": "Member created successfully",
  "email_sent": true,
  "email_error": null
}
```

---

### **GET /api/v1/members/list**

**Purpose**: Retrieve paginated list of members that current user can manage  
**Use Case**: Display team members in admin panels, generate reports  
**Why Created**: Core listing functionality with proper access control

**Business Logic**:

- Shows only members in the user's management hierarchy
- SuperAdmin sees all users, others see only their team
- Supports filtering by role, active status, and search terms
- Implements pagination for performance

**Query Parameters**:

- `page`: Page number (default: 1)
- `limit`: Items per page (1-100, default: 10)
- `role`: Filter by specific role
- `is_active`: Filter by active status (true/false)
- `search`: Search in name, email, or phone

**Response**:

```json
{
  "members": [
    {
      "id": 123,
      "user_code": "USR123",
      "full_name": "Jane Smith",
      "email": "jane@example.com",
      "role_name": "Manager",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 10
}
```

---

### **GET /api/v1/members/{member_id}**

**Purpose**: Get detailed information about a specific member  
**Use Case**: View member profile, edit forms, audit trails  
**Why Created**: Essential for detailed member management and data validation

**Business Logic**:

- Validates user has permission to view the requested member
- Returns comprehensive member information including wallet data
- Used for profile management and detailed reporting

---

### **PUT /api/v1/members/{member_id}**

**Purpose**: Update member information  
**Use Case**: Edit member profiles, update contact information  
**Why Created**: Essential CRUD operation for maintaining accurate member data

**Business Logic**:

- Validates edit permissions based on hierarchy
- Prevents unauthorized role changes
- Maintains audit trail of changes
- Handles email/phone uniqueness constraints

---

### **PATCH /api/v1/members/{member_id}/status**

**Purpose**: Update member active/inactive status  
**Use Case**: Deactivate problematic users, reactivate suspended accounts  
**Why Created**: Quick status management without full profile updates

**Business Logic**:

- Implements soft delete/restore functionality
- Maintains data integrity while managing access
- Used for account suspension and reactivation workflows

---

### **DELETE /api/v1/members/{member_id}**

**Purpose**: Delete a member (soft delete by deactivation)  
**Use Case**: Remove terminated employees, clean up test accounts  
**Why Created**: Safe deletion that preserves historical data

**Business Logic**:

- Performs soft delete to maintain referential integrity
- Preserves transaction history and audit trails
- Prevents actual data loss while removing access

---

## 🛡️ Admin Member Routes (`member_admin_routes.py`)

These endpoints provide advanced administrative features for complex member management operations.

### **POST /api/v1/members/admin/list**

**Purpose**: Enhanced member listing with advanced filters and admin-specific data  
**Use Case**: Comprehensive admin dashboards, detailed reporting, audit purposes  
**Why Created**: Regular listing doesn't include sensitive admin data like wallet balances, detailed hierarchy info

**Business Logic**:

- Returns enriched member data including wallet balances, transaction counts
- Includes parent-child relationship details
- Provides advanced filtering options for complex queries
- Supports export-ready data formats

**Features**:

- Wallet balance information
- Parent hierarchy visualization
- Advanced date range filtering
- Multi-role filtering
- Geographic filtering by state/city

---

### **POST /api/v1/members/admin/list/role-based**

**Purpose**: Role-specific member listing with enhanced hierarchy visualization  
**Use Case**: Managing specific teams, role-based reporting, hierarchy analysis  
**Why Created**: Different roles need different data views and management capabilities

**Business Logic**:

- Customizes data output based on requesting user's role
- Provides role-specific management actions
- Includes hierarchical relationship mapping
- Optimizes data for role-based workflows

---

### **POST /api/v1/members/admin/bulk-action**

**Purpose**: Perform bulk operations on multiple members simultaneously  
**Use Case**: Mass activation/deactivation, bulk role changes, group notifications  
**Why Created**: Administrative efficiency for managing large teams

**Business Logic**:

- Validates permissions for each selected member
- Implements transaction safety for bulk operations
- Provides detailed operation results and error handling
- Supports various bulk actions:
  - Bulk activation/deactivation
  - Bulk role changes (with hierarchy validation)
  - Bulk parent reassignment
  - Mass email notifications

**Supported Actions**:

- `activate`: Activate multiple members
- `deactivate`: Deactivate multiple members
- `change_role`: Change role for multiple members
- `reassign_parent`: Change parent for multiple members
- `send_notification`: Send bulk notifications

---

### **POST /api/v1/members/admin/export**

**Purpose**: Export member data in various formats (CSV, Excel, PDF)  
**Use Case**: Regulatory reporting, data backup, external system integration  
**Why Created**: Compliance requirements and data portability needs

**Business Logic**:

- Generates filtered exports based on criteria
- Includes comprehensive member data with proper formatting
- Supports multiple output formats
- Implements data privacy controls

**Export Options**:

- CSV: For spreadsheet analysis
- Excel: With formatted sheets and charts
- PDF: For official reports
- JSON: For system integration

---

### **GET /api/v1/members/admin/dashboard**

**Purpose**: Provide comprehensive statistics and metrics for member management  
**Use Case**: Executive dashboards, performance monitoring, trend analysis  
**Why Created**: Data-driven decision making requires aggregated insights

**Business Logic**:

- Calculates real-time member statistics
- Provides trend analysis and growth metrics
- Includes role distribution and hierarchy health
- Generates actionable insights for management

**Metrics Provided**:

- Total members by role
- Active/inactive ratios
- Recent registration trends
- Geographic distribution
- Hierarchy depth analysis
- Performance indicators

---

### **GET /api/v1/members/admin/schemes**

**Purpose**: Retrieve available schemes/plans for member creation  
**Use Case**: Dynamic form population, scheme management, product catalog  
**Why Created**: Business offers multiple membership schemes with different features

**Business Logic**:

- Returns active schemes available for new members
- Includes scheme details, pricing, and features
- Supports role-based scheme availability
- Used for dynamic form generation

---

### **GET /api/v1/members/admin/locations**

**Purpose**: Get hierarchical location data (states, cities) for member registration  
**Use Case**: Address validation, geographic filtering, location-based services  
**Why Created**: Standardized location data ensures consistency and enables geographic analysis

**Business Logic**:

- Provides standardized state and city lists
- Supports hierarchical location selection
- Enables geographic filtering and reporting
- Maintains data consistency across the system

---

### **GET /api/v1/members/admin/parents** ⭐ **FULLY IMPLEMENTED**

**Purpose**: Get available parent options for member creation based on role hierarchy  
**Use Case**: Parent selection dropdowns, hierarchy validation, role-based assignments  
**Why Created**: Complex role hierarchy requires intelligent parent selection based on permissions

**Business Logic**:

- Filters potential parents based on current user's permissions
- Implements role hierarchy rules (e.g., Agent can't be parent to Manager)
- Supports search functionality for large lists
- Validates hierarchy constraints in real-time

**Query Parameters**:

- `role`: Filter parents by specific role
- `search`: Search parents by name, email, or user code

**Response Example**:

```json
{
  "success": true,
  "parents": [
    {
      "id": 123,
      "name": "John Manager",
      "user_code": "USR123",
      "role_name": "Manager",
      "email": "john@example.com",
      "is_active": true
    }
  ],
  "message": "Found 5 potential parents"
}
```

---

### **GET /api/v1/members/admin/permissions** ⭐ **FULLY IMPLEMENTED**

**Purpose**: Get current user's role permissions and manageable roles  
**Use Case**: Dynamic UI rendering, permission validation, feature access control  
**Why Created**: Frontend needs to know what actions user can perform to show/hide features

**Business Logic**:

- Returns roles that current user can manage
- Lists roles that user can create
- Provides permission flags for UI control
- Enables dynamic feature rendering

**Response Example**:

```json
{
  "current_role": "Manager",
  "manageable_roles": ["Agent", "Customer"],
  "creatable_roles": ["Agent", "Customer"],
  "can_create": true,
  "can_manage": true
}
```

---

## 🏗️ System Architecture Benefits

### **Why Two Router Files?**

1. **Separation of Concerns**: Core operations vs. advanced admin features
2. **Performance**: Basic operations don't load heavy admin features
3. **Security**: Different permission levels and access controls
4. **Scalability**: Easy to extend admin features without affecting core functionality
5. **Maintenance**: Easier debugging and feature development

### **Role-Based Access Control**

The system implements sophisticated RBAC:

- **SuperAdmin**: Full system access, can manage all users and roles
- **Admin**: Can manage lower-level roles within their organization
- **Manager**: Can manage agents and customers in their team
- **Agent**: Can manage assigned customers
- **Customer**: Self-service operations only

### **Hierarchy Management**

The parent-child relationship system enables:

- Commission distribution chains
- Territory management
- Team organization
- Reporting structures
- Permission inheritance

---

## 🚀 Implementation Status

### ✅ **Fully Implemented**

- All Core Member Routes (CRUD operations)
- Parent selection endpoint
- Permission management endpoint
- Role-based access control
- Hierarchy validation

### 🔄 **Placeholder/Planned**

- Advanced admin listing with wallet data
- Bulk operations framework
- Export functionality
- Dashboard statistics
- Scheme management
- Location data management

---

## 🎯 Business Value

### **For Admins**

- Efficient team management
- Comprehensive reporting
- Bulk operations for productivity
- Real-time dashboard insights

### **For Managers**

- Team overview and control
- Performance tracking
- Hierarchy management
- Quick status updates

### **For the Business**

- Scalable user management
- Audit trail maintenance
- Compliance reporting
- Data-driven insights
- Operational efficiency

### **For Developers**

- Clean, maintainable code
- Modular architecture
- Easy feature extension
- Comprehensive API documentation

---

## 📋 API Usage Examples

### **Creating a New Agent**

```bash
POST /api/v1/members/create
{
  "full_name": "New Agent",
  "email": "agent@example.com",
  "phone": "9876543210",
  "role_name": "Agent",
  "parent_id": 123,
  "state": "Karnataka",
  "city": "Bangalore"
}
```

### **Listing Team Members**

```bash
GET /api/v1/members/list?page=1&limit=20&role=Agent&is_active=true
```

### **Getting Parent Options**

```bash
GET /api/v1/members/admin/parents?role=Manager&search=john
```

### **Bulk Deactivation**

```bash
POST /api/v1/members/admin/bulk-action
{
  "action": "deactivate",
  "member_ids": [123, 456, 789],
  "reason": "End of contract"
}
```

This comprehensive API structure provides all the necessary tools for effective member management while maintaining security, scalability, and ease of use.
