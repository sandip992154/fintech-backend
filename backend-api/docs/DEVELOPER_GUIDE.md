# Developer Setup Guide

## 🚀 Quick Start for Developers

This guide will help new developers get up and running with the Bandru Financial Services API.

## 📋 Prerequisites

Before you begin, ensure you have:
- Python 3.13.1 installed
- Git installed
- VS Code or your preferred IDE
- Postman (optional, for API testing)

## 🛠️ Development Environment Setup

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone https://github.com/BandaruPay/backend-api.git
cd backend-api

# Create virtual environment
python -m venv bandruenv

# Activate virtual environment
# Windows:
bandruenv\Scripts\activate
# Linux/Mac:
source bandruenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup
```bash
# Initialize database
python scripts/initial_setup.py

# Run migrations (if any)
alembic upgrade head
```

### Step 3: Configuration
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=sqlite:///./app.db

# JWT Settings
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

### Step 4: Run the Application
```bash
# Start the development server
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing Setup

### Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run tests with coverage
python -m pytest tests/ --cov=services --cov-report=html
```

### Test Database
The tests use a separate test database (`test.db`) to avoid affecting development data.

## 📁 Project Structure Overview

```
backend-api/
├── services/              # Core business logic
│   ├── auth/             # Authentication services
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── routers/          # API route handlers
│   └── business/         # Business logic
├── database/             # Database configuration
├── utils/                # Utility functions
├── config/               # Configuration files
├── tests/                # Test suites
├── logs/                 # Application logs
├── scripts/              # Setup and utility scripts
└── docs/                 # Documentation
```

## 🔧 Development Tools

### Recommended VS Code Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "charliermarsh.ruff",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml"
  ]
}
```

### Pre-commit Hooks (Optional)
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 🎯 Common Development Tasks

### Adding a New API Endpoint

1. **Define the schema** in `services/schemas/`
2. **Create the model** in `services/models/` (if needed)
3. **Add business logic** in `services/business/`
4. **Create the router** in `services/routers/`
5. **Write tests** in `tests/`

### Adding a New Role
1. Update `ROLE_HIERARCHY` in `services/auth/auth.py`
2. Update schema validation in `services/schemas/schemas.py`
3. Add tests for the new role

### Database Changes
1. Modify models in `services/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review and edit migration file
4. Apply migration: `alembic upgrade head`

## 🐛 Debugging

### Enable Debug Mode
Set `DEBUG=True` in your `.env` file for detailed error messages.

### Log Files
Check `logs/app.log` for application logs and `logs/error.log` for errors.

### Database Inspection
```bash
# Open SQLite database
sqlite3 app.db

# View tables
.tables

# View schema
.schema users
```

## 📊 API Testing

### Using Postman
Import the collection: `Bandru_API.postman_collection.json`

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password","role":"customer"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password"}'
```

## ⚡ Performance Tips

1. **Use async/await** for I/O operations
2. **Implement database connection pooling**
3. **Add request/response caching** where appropriate
4. **Monitor database query performance**
5. **Use pagination** for large datasets

## 🔒 Security Considerations

1. **Never commit secrets** to version control
2. **Use environment variables** for configuration
3. **Validate all inputs** using Pydantic schemas
4. **Implement proper error handling**
5. **Follow role-based access control**

## 📞 Getting Help

1. **Check the documentation**: `/docs` endpoint when running
2. **Read the code**: Well-commented codebase
3. **Run tests**: Understand expected behavior
4. **Ask questions**: Create issues on GitHub

## 🔄 Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Make changes**: Follow coding standards
3. **Write tests**: Ensure good coverage
4. **Run tests**: `python -m pytest tests/`
5. **Commit changes**: Use descriptive messages
6. **Push branch**: `git push origin feature/your-feature`
7. **Create pull request**: For code review

Happy coding! 🚀
