# BandruPay - Local Development Startup Guide

## Prerequisites

You need the following installed on your system:
- Python 3.10+ (currently have Python 3.14)
- Node.js 16+ and npm
- PostgreSQL (for database)

## Environment Setup

### Backend Setup

#### 1. Install Python Dependencies

```bash
cd backend-api

# Install all required packages
pip install psycopg2-binary python-dotenv fastapi uvicorn sqlalchemy pydantic python-jose passlib bcrypt

# Or install all from requirements.txt (if network is available)
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Create a `.env` file in `backend-api/` directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:root@localhost:5432/bandaru_pay

# Email Configuration
MAIL_FROM=noreply@bandarupay.com
MAIL_PASSWORD=your_email_password

# JWT Configuration
SECRET_KEY=your_secret_key_here_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# OTP Configuration
OTP_EXPIRY_MINUTES=10
OTP_COOLDOWN_MINUTES=1
MAX_OTP_ATTEMPTS=5

# Superadmin Configuration
SUPERADMIN_EMAIL=admin@bandarupay.com
SUPERADMIN_PASSWORD=SuperAdmin@123
```

#### 3. Start Backend Server

```bash
cd backend-api
python main.py

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

Backend will be available at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

---

### Frontend Setup

#### 1. Install Node Dependencies

```bash
cd superadmin

# Remove node_modules if installation failed
rm -r node_modules package-lock.json

# Install dependencies
npm install
```

#### 2. Configure Frontend Environment

Create a `.env.local` file in `superadmin/` directory:

```bash
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

#### 3. Start Frontend Development Server

```bash
cd superadmin
npm run dev

# Expected output:
#   VITE v6.x.x  build 0.00s
#   ➜  Local:   http://localhost:5173/
#   ➜  press h to show help
```

Frontend will be available at: **http://localhost:5173**

---

## Database Setup

### Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE bandaru_pay;

# Create user
CREATE USER bandru_pay_user WITH PASSWORD 'yjQLHh9TZoVF2eaJUcBzKh9nv2jWE7ab';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE bandaru_pay TO bandru_pay_user;

# Exit
\q
```

### Run Database Migrations

```bash
cd backend-api
alembic upgrade head
```

---

## Testing the Setup

### 1. Test Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-05T10:30:00",
  "version": "1.0.0",
  "database": "connected"
}
```

### 2. Test Login Flow

```bash
# Login with superadmin credentials
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=superadmin&password=SuperAdmin@123"
```

### 3. Access Frontend

Open browser and navigate to: **http://localhost:5173**

Login with:
- **Email/Username:** superadmin
- **Password:** SuperAdmin@123

---

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution:** Install psycopg2-binary
```bash
pip install psycopg2-binary --upgrade
```

### Issue: `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Install FastAPI
```bash
pip install fastapi uvicorn
```

### Issue: Port 8000 already in use

**Solution:** Kill the process or use different port
```bash
# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# On Mac/Linux
lsof -i :8000
kill -9 <PID>
```

### Issue: npm install fails with permission errors

**Solution:** Clear cache and retry
```bash
cd superadmin
rm -r node_modules package-lock.json
npm cache clean --force
npm install
```

### Issue: Database connection refused

**Solution:** Verify PostgreSQL is running
```bash
# Windows
Get-Service postgresql*

# Mac
brew services list | grep postgres

# Linux
sudo systemctl status postgresql
```

---

## Project Endpoints

### Backend (FastAPI)

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `POST /auth/login` | User login (sends OTP) |
| `POST /auth/login-otp-verify` | OTP verification |
| `POST /auth/register` | User registration |
| `GET /auth/me` | Get current user |
| `GET /docs` | API documentation (Swagger UI) |
| `GET /redoc` | API documentation (ReDoc) |

### Frontend (React)

| URL | Purpose |
|-----|---------|
| `http://localhost:5173/` | Login page |
| `http://localhost:5173/dashboard` | Admin dashboard |
| `http://localhost:5173/users` | User management |
| `http://localhost:5173/schemes` | Scheme management |

---

## Development Workflow

### 1. Start Backend
```bash
cd backend-api
python main.py
```

### 2. Start Frontend (in new terminal)
```bash
cd superadmin
npm run dev
```

### 3. Open Browser
Navigate to: **http://localhost:5173**

### 4. Access API Docs
Navigate to: **http://localhost:8000/docs**

---

## Stopping Services

### Stop Backend
Press `Ctrl+C` in backend terminal

### Stop Frontend
Press `Ctrl+C` in frontend terminal

---

## Additional Commands

### Build Frontend for Production
```bash
cd superadmin
npm run build
npm run preview
```

### Run Tests
```bash
# Backend tests
cd backend-api
pytest

# Frontend tests
cd superadmin
npm run test
```

### Linting
```bash
# Frontend linting
cd superadmin
npm run lint
```

---

## Notes

- **Backend auto-reloads** when code changes (reload=True in uvicorn)
- **Frontend auto-reloads** with Vite hot module replacement
- **Database** is PostgreSQL (ensure it's running)
- **Ports:** Backend=8000, Frontend=5173
- **API Base URL** for frontend: http://localhost:8000

---

## Support

For issues or questions:
1. Check the logs in terminal
2. Verify all prerequisites are installed
3. Review the FULL_AUDIT_REPORT.md for bug fixes
4. Check API documentation at http://localhost:8000/docs

---

Generated: February 5, 2026
