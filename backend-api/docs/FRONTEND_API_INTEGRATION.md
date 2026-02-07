# Member Management APIs for Frontend Integration

## Overview

This document provides the complete API endpoints for integrating with the member management admin panel shown in the UI design.

## Base URL

```
/api/v1/members
```

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

## 1. Enhanced Member List (Admin Panel)

### Endpoint

```
POST /api/v1/members/admin/list
```

### Request Body

```json
{
  "page": 1,
  "limit": 10,
  "from_date": "2024-01-01T00:00:00",
  "to_date": "2024-12-31T23:59:59",
  "search_value": "search term",
  "agent_parent": "BANDADM00001",
  "status": "active",
  "role": "retailer",
  "is_active": true
}
```

### Response

```json
{
  "members": [
    {
      "id": 13,
      "user_code": "BANDADM00001",
      "full_name": "Admin User",
      "email": "admin@example.com",
      "phone": "9876543210",
      "mobile": "9876543210",
      "role": "admin",
      "role_name": "admin",
      "is_active": true,
      "created_at": "2024-06-25T11:35:00",
      "updated_at": "2024-06-25T11:35:00",
      "parent_details": {
        "user_code": "BANDSA000001",
        "full_name": "Super Admin",
        "phone": "9999999999",
        "role": "super_admin"
      },
      "company_profile": {
        "company_pan": "ABCDE1234F",
        "shop_name": "Admin Shop",
        "scheme": "Premium",
        "registration_date": "01/04/2023"
      },
      "wallet_details": {
        "main_balance": 0.0,
        "aeps_balance": 0.0,
        "commission_balance": 0.2,
        "total_balance": 0.2
      },
      "id_stock": {
        "admin_count": 1,
        "md_count": 1,
        "distributor_count": 1,
        "retailer_count": 1
      },
      "status": "active"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false,
  "summary": {
    "total_active": 1,
    "total_inactive": 0,
    "total_wallet_balance": 0.2
  }
}
```

## 2. Create New Member

### Endpoint

```
POST /api/v1/members/create
```

### Request Body

```json
{
  "full_name": "New Member",
  "email": "member@example.com",
  "phone": "9876543210",
  "mobile": "9876543210",
  "role_name": "retailer",
  "address": "123 Main Street",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pin_code": "400001",
  "shop_name": "Member Shop",
  "scheme": "Premium",
  "pan_card_number": "ABCDE1234F",
  "aadhaar_card_number": "123456789012",
  "company_pan_card": "FGHIJ5678K"
}
```

### Response

```json
{
  "member": {
    "id": 14,
    "user_code": "BANDRET00002",
    "full_name": "New Member",
    "email": "member@example.com",
    "role": "retailer"
  },
  "message": "Retailer member created successfully. Login credentials sent to email.",
  "success": true
}
```

## 3. Get Schemes

### Endpoint

```
GET /api/v1/members/schemes
```

### Response

```json
{
  "schemes": [
    {
      "id": "premium",
      "name": "Premium Plan",
      "description": "Premium commission structure",
      "commission_rate": 2.5,
      "is_active": true
    },
    {
      "id": "standard",
      "name": "Standard Plan",
      "description": "Standard commission structure",
      "commission_rate": 2.0,
      "is_active": true
    }
  ],
  "total": 2
}
```

## 4. Get Location Data

### Endpoint

```
GET /api/v1/members/locations
GET /api/v1/members/locations?state_id=MH
```

### Response

```json
{
  "states": [
    {
      "id": "MH",
      "name": "Maharashtra",
      "code": "MH"
    },
    {
      "id": "DL",
      "name": "Delhi",
      "code": "DL"
    }
  ],
  "cities": [
    {
      "id": "mumbai",
      "name": "Mumbai",
      "state_id": "MH"
    },
    {
      "id": "pune",
      "name": "Pune",
      "state_id": "MH"
    }
  ]
}
```

## 5. Get Parent/Agent Options

### Endpoint

```
GET /api/v1/members/admin/parents
GET /api/v1/members/admin/parents?role=retailer&search=admin
```

### Response

```json
{
  "success": true,
  "parents": [
    {
      "id": 1,
      "user_code": "BANDADM00001",
      "full_name": "Admin User",
      "role": "admin",
      "phone": "9876543210"
    }
  ],
  "total": 1
}
```

## 6. Dashboard Statistics

### Endpoint

```
GET /api/v1/members/admin/dashboard
```

### Response

```json
{
  "total_members": 150,
  "active_members": 140,
  "inactive_members": 10,
  "pending_kyc": 25,
  "completed_kyc": 125,
  "role_distribution": {
    "admin": 2,
    "distributor": 15,
    "retailer": 80,
    "customer": 53
  },
  "recent_registrations": 12,
  "recent_activations": 8,
  "total_wallet_balance": 150000.5
}
```

## 7. Export Members

### Endpoint

```
POST /api/v1/members/admin/export
```

### Request Body

```json
{
  "format": "excel",
  "filters": {
    "page": 1,
    "limit": 1000,
    "role": "retailer",
    "is_active": true
  },
  "columns": ["user_code", "full_name", "email", "phone", "role"]
}
```

### Response

```json
{
  "success": true,
  "message": "Export initiated for excel format",
  "download_url": "/downloads/members_export_20241004_143000.excel"
}
```

## 8. Bulk Actions

### Endpoint

```
POST /api/v1/members/admin/bulk-action
```

### Request Body

```json
{
  "member_ids": [1, 2, 3],
  "action": "activate",
  "reason": "Bulk activation"
}
```

### Response

```json
{
  "success": true,
  "message": "Successfully activated 3 members",
  "processed_count": 3,
  "failed_count": 0,
  "failed_items": []
}
```

## 9. Member Search (Autocomplete)

### Endpoint

```
GET /api/v1/members/admin/member-search?q=admin&limit=10
```

### Response

```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "user_code": "BANDADM00001",
      "full_name": "Admin User",
      "role": "admin",
      "email": "admin@example.com",
      "phone": "9876543210",
      "is_active": true
    }
  ],
  "total": 1
}
```

## 10. Get Role Permissions

### Endpoint

```
GET /api/v1/members/role-permissions
```

### Response

```json
{
  "current_role": "admin",
  "level": 1,
  "creatable_roles": [
    "whitelabel",
    "mds",
    "distributor",
    "retailer",
    "customer"
  ],
  "manageable_roles": [
    "whitelabel",
    "mds",
    "distributor",
    "retailer",
    "customer"
  ],
  "hierarchy": [
    {
      "role": "super_admin",
      "level": 0,
      "description": "Super Administrator with full system access",
      "can_create": [
        "admin",
        "whitelabel",
        "mds",
        "distributor",
        "retailer",
        "customer"
      ],
      "manageable_roles": [
        "admin",
        "whitelabel",
        "mds",
        "distributor",
        "retailer",
        "customer"
      ]
    }
  ]
}
```

## Frontend Integration Notes

### For Admin List Page:

1. Use `POST /api/v1/members/admin/list` for the main table data
2. Implement date range filters using `from_date` and `to_date`
3. Use `search_value` for the search input
4. Use `agent_parent` for parent/agent dropdown filter
5. Use `status` and `is_active` for status filters
6. Implement pagination using `page` and `limit`

### For Add New Member Form:

1. Use `GET /api/v1/members/schemes` to populate scheme dropdown
2. Use `GET /api/v1/members/locations` to populate state dropdown
3. Use `GET /api/v1/members/locations?state_id=XX` to populate city dropdown
4. Use `GET /api/v1/members/admin/parents` for parent selection
5. Use `POST /api/v1/members/create` to submit the form

### For Export Functionality:

1. Use `POST /api/v1/members/admin/export` with current filters
2. Handle the download URL response

### For Dashboard:

1. Use `GET /api/v1/members/admin/dashboard` for statistics
2. Display role distribution charts
3. Show recent activity metrics

All APIs include proper error handling and follow RESTful conventions. The responses include success/error status and descriptive messages for frontend display.
