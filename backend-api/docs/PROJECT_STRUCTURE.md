# Project Structure Guide

## 📁 Optimized Project Structure

The project has been reorganized with a clean, scalable structure that follows industry best practices:

```
backend-api/
├── 📁 app/                          # Main application package
│   ├── __init__.py                  # App package init
│   ├── main.py                      # FastAPI app creation and configuration
│   │
│   ├── 📁 core/                     # Core application components
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration settings
│   │   ├── database.py              # Database configuration
│   │   ├── logging_config.py        # Logging setup and middleware
│   │   ├── security.py              # Security utilities (planned)
│   │   └── exceptions.py            # Custom exceptions (planned)
│   │
│   ├── 📁 api/                      # API layer
│   │   ├── __init__.py
│   │   └── 📁 v1/                   # API version 1
│   │       ├── __init__.py
│   │       ├── router.py            # Main API router aggregation
│   │       └── 📁 endpoints/        # Individual endpoint modules
│   │           ├── __init__.py
│   │           ├── auth.py          # Authentication endpoints
│   │           ├── users.py         # User management endpoints
│   │           ├── transactions.py  # Transaction endpoints
│   │           └── services.py      # Financial services endpoints
│   │
│   ├── 📁 models/                   # Database models (planned migration)
│   ├── 📁 schemas/                  # Pydantic schemas (planned migration)
│   ├── 📁 services/                 # Business logic (planned migration)
│   └── 📁 utils/                    # Utility functions (planned migration)
│
├── 📁 services/                     # Current business logic (legacy)
│   ├── 📁 auth/                     # Authentication services
│   ├── 📁 models/                   # Database models
│   ├── 📁 schemas/                  # Pydantic schemas
│   ├── 📁 routers/                  # API routers (legacy)
│   └── 📁 business/                 # Business logic
│
├── 📁 tests/                        # Test suites
│   ├── conftest.py                  # Test configuration
│   ├── test_auth.py                 # Authentication tests
│   ├── test_transactions.py         # Transaction tests
│   └── test_additional_services.py  # Service tests
│
├── 📁 docs/                         # Documentation
│   ├── README.md                    # Main project documentation
│   ├── DEVELOPER_GUIDE.md           # Development setup guide
│   ├── API_REFERENCE.md             # API documentation
│   └── ARCHITECTURE.md              # System architecture (planned)
│
├── 📁 config/                       # Configuration files
├── 📁 database/                     # Database utilities
├── 📁 utils/                        # General utilities
├── 📁 logs/                         # Application logs
├── 📁 scripts/                      # Utility scripts
├── 📁 static/                       # Static files
├── 📁 migrations/                   # Database migrations (Alembic)
│
├── main.py                          # Legacy main file (kept for compatibility)
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables
├── alembic.ini                     # Database migration config
├── docker-compose.yml              # Docker configuration
├── Dockerfile                      # Docker build file
└── README.md                       # Project overview
```

## 🏗️ Architecture Benefits

### 1. **Separation of Concerns**
- **app/core/**: Core functionality (config, database, logging)
- **app/api/**: API layer with versioning support
- **app/models/**: Database models
- **app/schemas/**: Data validation schemas
- **app/services/**: Business logic

### 2. **Scalability**
- API versioning (`/api/v1/`, `/api/v2/`)
- Modular endpoint organization
- Clear dependency injection patterns
- Easy to add new features

### 3. **Maintainability**
- Clear file organization
- Consistent naming conventions
- Comprehensive documentation
- Type hints throughout

### 4. **Developer Experience**
- Easy to understand structure
- Clear import paths
- Comprehensive documentation
- Development tools integration

## 🔧 Configuration Management

### Environment-Based Configuration
All settings are managed through environment variables with sensible defaults:

```python
# app/core/config.py
class Settings(BaseSettings):
    PROJECT_NAME: str = "Bandru Financial Services API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
```

### Role-Based Configuration
Centralized role hierarchy and permissions:

```python
ROLE_HIERARCHY = {
    "super_admin": 1,
    "admin": 2,
    "whitelabel": 3,
    "mds": 4,
    "distributor": 5,
    "retailer": 6,
    "customer": 7
}

ROLE_PERMISSIONS = {
    "super_admin": ["read:all", "write:all", "delete:all"],
    "admin": ["read:all", "write:users", "read:transactions"],
    # ... more roles
}
```

## 📊 Database Management

### Enhanced Database Configuration
```python
# app/core/database.py
class DatabaseManager:
    def get_session(self) -> Session:
        """Get a new database session"""
        
    def execute_raw_sql(self, sql: str, params: dict = None):
        """Execute raw SQL query"""
        
    def backup_database(self, backup_path: str):
        """Create database backup"""
        
    def check_connection(self) -> bool:
        """Check database connection"""
```

### Session Management
```python
@contextmanager
def session_scope():
    """Transactional scope for database operations"""
    
def get_db() -> Session:
    """FastAPI dependency for database sessions"""
```

## 📝 Logging System

### Structured Logging
```python
# app/core/logging_config.py
class StructuredLogger:
    def log_user_action(self, user_id: int, action: str, details: dict = None):
        """Log user actions with structured format"""
        
    def log_transaction(self, transaction_id: str, user_id: int, amount: float):
        """Log transactions with structured format"""
        
    def log_security_event(self, event_type: str, user_id: int = None):
        """Log security events"""
```

### Request/Response Middleware
```python
class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive request/response logging"""
```

## 🛣️ API Design

### Versioned API Structure
```
/api/v1/auth/         # Authentication endpoints
/api/v1/users/        # User management
/api/v1/transactions/ # Transaction management
/api/v1/services/     # Financial services
```

### Consistent Response Format
```python
# Success Response
{
    "status": "success",
    "data": {...},
    "message": "Operation completed"
}

# Error Response
{
    "detail": "Error message",
    "error_code": "ERROR_CODE",
    "timestamp": "2025-08-17T00:00:00Z"
}
```

## 🧪 Testing Structure

### Comprehensive Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Authentication Tests**: Role-based access testing
- **Service Tests**: External service integration

### Test Organization
```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_auth.py            # Authentication tests (21 tests)
├── test_transactions.py    # Transaction tests (6 tests)
├── test_additional_services.py # Service tests (7 tests)
└── test_api_integration.py # Integration tests
```

## 📋 Development Guidelines

### Code Standards
- **Type Hints**: All functions have type annotations
- **Docstrings**: Comprehensive documentation
- **Error Handling**: Proper exception handling
- **Validation**: Pydantic schema validation

### Import Organization
```python
# Standard library imports
from typing import List, Dict, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Local imports
from app.core.config import settings
from app.core.database import get_db
```

## 🚀 Deployment Ready

### Docker Support
- Multi-stage Docker builds
- Production-ready configurations
- Environment variable management
- Health checks

### Environment Configurations
- **Development**: Debug mode, detailed logging
- **Staging**: Production-like settings
- **Production**: Optimized for performance and security

## 📞 Getting Started

### Quick Start
1. **Clone and Setup**: `git clone <repo> && cd backend-api`
2. **Environment**: Create `.env` file with your settings
3. **Install**: `pip install -r requirements.txt`
4. **Run**: `python app/main.py`
5. **Test**: `python -m pytest tests/ -v`

### Development Workflow
1. **Feature Branch**: `git checkout -b feature/new-feature`
2. **Develop**: Add code with tests
3. **Test**: `python -m pytest tests/`
4. **Document**: Update relevant documentation
5. **Pull Request**: Submit for review

This optimized structure provides a solid foundation for continued development and makes the codebase much more accessible to new developers! 🎉
