# Bandru Financial Services API Documentation

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Setup & Installation](#setup--installation)
- [API Documentation](#api-documentation)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Deployment](#deployment)

## 🚀 Project Overview

Bandru Financial Services API is a comprehensive fintech backend built with FastAPI, providing:

- **Role-Based Authentication** with 7-tier hierarchy
- **Transaction Management** (Wallet, Transfers, History)
- **Financial Services** (AEPS, mATM, Insurance, PAN, FASTag)
- **Secure JWT Authentication**
- **RESTful API Design**

## 🏗️ Architecture

### Tech Stack

- **Framework**: FastAPI 0.116.1
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with role-based permissions
- **Testing**: Pytest with 100% test coverage
- **Environment**: Python 3.13.1

### Role Hierarchy

1. **super_admin** (Level 1) - Highest privileges
2. **admin** (Level 2) - Administrative access
3. **whitelabel** (Level 3) - White-label partner access
4. **mds** (Level 4) - Master Distributor access
5. **distributor** (Level 5) - Distributor access
6. **retailer** (Level 6) - Retailer access
7. **customer** (Level 7) - End customer access

## 📁 Project Structure

```
backend-api/
├── docs/                    # Documentation
├── app/                     # Application core
│   ├── __init__.py
│   ├── main.py             # FastAPI app initialization
│   ├── config/             # Configuration management
│   ├── core/               # Core functionality
│   │   ├── auth.py         # Authentication logic
│   │   ├── security.py     # Security utilities
│   │   └── exceptions.py   # Custom exceptions
│   ├── api/                # API routes
│   │   ├── v1/             # API version 1
│   │   │   ├── auth.py     # Auth endpoints
│   │   │   ├── users.py    # User endpoints
│   │   │   ├── transactions.py
│   │   │   └── services.py
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
├── tests/                  # Test suites
├── migrations/             # Database migrations
├── scripts/                # Utility scripts
├── logs/                   # Application logs
└── requirements/           # Dependencies
```

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.13.1
- Git

### Installation Steps

1. **Clone Repository**

```bash
git clone https://github.com/BandaruPay/backend-api.git
cd backend-api
```

2. **Create Virtual Environment**

```bash
python -m venv bandruenv
bandruenv\Scripts\activate  # Windows
source bandruenv/bin/activate  # Linux/Mac
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Setup Database**

```bash
alembic upgrade head
```

5. **Run Application**

```bash
python app/main.py
```

### Environment Variables

Create `.env` file:

```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./app.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## 📚 API Documentation

### Authentication Endpoints

- `POST /auth/register` - User registration with role
- `POST /auth/login` - User login with JWT token
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user info

### User Management

- `GET /users/` - List users (admin only)
- `GET /users/{user_id}` - Get user details
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### Transactions

- `POST /transactions/wallet/create` - Create wallet
- `POST /transactions/wallet/topup` - Wallet top-up
- `POST /transactions/transfer` - Money transfer
- `GET /transactions/history` - Transaction history

### Financial Services

- `POST /services/aeps/balance` - AEPS balance inquiry
- `POST /services/aeps/withdrawal` - AEPS cash withdrawal
- `POST /services/matm/initialize` - mATM initialization
- `POST /services/insurance/quotes` - Insurance quotes
- `POST /services/pan/apply` - PAN card application
- `POST /services/fastag/recharge` - FASTag recharge

## 👥 Development Guidelines

### Code Style

- Follow PEP 8 standards
- Use type hints
- Write descriptive docstrings
- Maximum line length: 88 characters

### Git Workflow

- Create feature branches: `feature/feature-name`
- Write meaningful commit messages
- Submit pull requests for review

### Database Changes

- Create migrations for schema changes
- Test migrations thoroughly
- Never delete migrations

## 🧪 Testing

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Test Coverage

```bash
python -m pytest tests/ --cov=app --cov-report=html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Authentication Tests**: Role-based access testing

## 🚀 Deployment

### Docker Deployment

```bash
docker build -t bandru-api .
docker run -p 8000:8000 bandru-api
```

### Production Checklist

- [ ] Set secure SECRET_KEY
- [ ] Configure production database
- [ ] Setup HTTPS
- [ ] Configure logging
- [ ] Setup monitoring
- [ ] Backup strategy

## 📞 Support

For support and questions:

- **Email**: support@bandarupay.com
- **Documentation**: `/docs` endpoint
- **API Reference**: `/redoc` endpoint

## 📄 License

Copyright (c) 2025 BandaruPay. All rights reserved.

{
"items": [
{
"name": "Bandaru Pay",
"description": "Fin tech pay slab.",
"id": 7,
"is_active": true,
"created_by": 1,
"owner_id": null,
"created_by_role": "user",
"shared_with_users": null,
"shared_with_roles": null,
"created_at": "2025-10-02T16:39:29.684777",
"updated_at": "2025-10-02T16:40:15.460455"
},
{
"name": "NK tax consulatancy",
"description": "cbn n nbcnccz nnn",
"id": 6,
"is_active": true,
"created_by": 1,
"owner_id": null,
"created_by_role": "user",
"shared_with_users": null,
"shared_with_roles": null,
"created_at": "2025-10-02T16:28:33.281933",
"updated_at": "2025-10-02T16:34:22.180158"
},
{
"name": "AEPS Standard Scheme",
"description": "Slab-based commission scheme for AEPS transactions",
"id": 5,
"is_active": true,
"created_by": 14,
"owner_id": null,
"created_by_role": "user",
"shared_with_users": null,
"shared_with_roles": null,
"created_at": "2025-10-02T14:01:44.953045",
"updated_at": "2025-10-02T17:07:32.913984"
},
{
"name": "Utility Bill Payments",
"description": "Commission scheme for utility bill payments",
"id": 4,
"is_active": false,
"created_by": 14,
"owner_id": null,
"created_by_role": "user",
"shared_with_users": null,
"shared_with_roles": null,
"created_at": "2025-10-02T14:01:44.953042",
"updated_at": "2025-10-02T16:52:07.735876"
},
{
"name": "Premium DTH Package",
"description": "Premium commission scheme for DTH recharge services",
"id": 3,
"is_active": true,
"created_by": 14,
"owner_id": null,
"created_by_role": "user",
"shared_with_users": null,
"shared_with_roles": null,
"created_at": "2025-10-02T14:01:44.953039",
"updated_at": "2025-10-02T16:52:21.764567"
},
{
"name": "Standard Mobile Recharge",
"description": "Standard commission scheme for mobile recharge services",
"id": 2,
"is_active": true,
"created_by": 14,
"owner_id": null,
"created_by_role": "user",
"shared_with_users": null,
"shared_with_roles": null,
"created_at": "2025-10-02T14:01:44.953032",
"updated_at": "2025-10-02T16:41:38.902148"
}
],
"total": 6,
"page": 1,
"size": 20,
"pages": 1
}
