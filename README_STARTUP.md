# 🚀 How to Run BandruPay Locally

## Quick Start (Recommended)

### Windows Users:

#### Option 1: One-Click Start (Easiest)
Double-click: **`START.bat`** in the project root folder

OR

#### Option 2: PowerShell
Open PowerShell and run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\START.ps1
```

---

### Mac/Linux Users:

Create a startup script or run manually:

```bash
# Terminal 1: Backend
cd backend-api
pip install psycopg2-binary python-dotenv fastapi uvicorn sqlalchemy pydantic python-jose passlib bcrypt
python main.py

# Terminal 2: Frontend
cd superadmin
npm install
npm run dev
```

---

## What Gets Started

### Backend (FastAPI)
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Port:** 8000
- **Auto-reload:** ✓ Yes (code changes auto-reload)

### Frontend (React + Vite)
- **URL:** http://localhost:5173
- **Port:** 5173
- **Hot Module Reload:** ✓ Yes (code changes instant update)

---

## First Time Setup

### 1. Install Python (if not already installed)
- Download from: https://www.python.org/downloads/
- **Important:** Add Python to PATH during installation

### 2. Install Node.js (if not already installed)
- Download from: https://nodejs.org/
- **Important:** Add to PATH during installation

### 3. Verify Installation
```bash
python --version    # Should show 3.10 or higher
node --version      # Should show 16.0 or higher
npm --version       # Should show 8.0 or higher
```

### 4. Start the Application
Use `START.bat` (Windows) or `START.ps1` (Windows PowerShell) or the manual steps above

---

## Login Credentials

Once the application is running:

1. Open browser: **http://localhost:5173**
2. Login with:
   - **Email/Username:** `superadmin`
   - **Password:** `SuperAdmin@123`

3. An OTP will be sent to: `noreply@bandarupay.com` (configure in backend)
4. Enter the OTP to complete login

---

## Database Configuration

Your backend is configured to use a **cloud PostgreSQL database** on Render.com:
- **Host:** dpg-d3d1jjb7mgec73auv4kg-a.oregon-postgres.render.com
- **Database:** bandru_pay
- **User:** bandru_pay_user

If you want to use a **local PostgreSQL database** instead:

### 1. Install PostgreSQL Locally
- https://www.postgresql.org/download/

### 2. Create Local Database
```bash
# Open PostgreSQL terminal
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

### 3. Update Backend Configuration
Edit `backend-api/database/database.py`:

**Change from:**
```python
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://...")  # Render.com
```

**To:**
```python
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bandru_pay_user:yjQLHh9TZoVF2eaJUcBzKh9nv2jWE7ab@localhost:5432/bandaru_pay")
```

### 4. Run Database Migrations
```bash
cd backend-api
alembic upgrade head
```

---

## Environment Variables

### Backend (.env file)
Create `backend-api/.env`:

```env
# Database
DATABASE_URL=postgresql://bandru_pay_user:yjQLHh9TZoVF2eaJUcBzKh9nv2jWE7ab@localhost:5432/bandaru_pay

# JWT/Security
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# OTP Settings
OTP_EXPIRY_MINUTES=10
OTP_COOLDOWN_MINUTES=1
MAX_OTP_ATTEMPTS=5

# Email (Optional - for sending OTPs)
MAIL_FROM=noreply@bandarupay.com
MAIL_PASSWORD=your_email_app_password

# Superadmin
SUPERADMIN_EMAIL=admin@bandarupay.com
SUPERADMIN_PASSWORD=SuperAdmin@123
```

### Frontend (.env.local)
Create `superadmin/.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

---

## Troubleshooting

### "Port 8000 already in use"
```bash
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "psycopg2 not found"
```bash
pip install psycopg2-binary --upgrade
```

### "npm install fails"
```bash
cd superadmin
rm -r node_modules package-lock.json
npm cache clean --force
npm install
```

### "Database connection refused"
- Verify your PostgreSQL database is running
- Check DATABASE_URL is correct
- Ensure psycopg2-binary is installed

### "Frontend won't load"
- Check http://localhost:5173 is running
- Check browser console (F12) for errors
- Verify backend is accessible at http://localhost:8000/health

---

## Testing the Setup

### Test Backend Health
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-05T...",
  "version": "1.0.0",
  "database": "connected"
}
```

### Test Login Flow
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=superadmin&password=SuperAdmin@123"
```

Should return OTP sent to email.

### Test API Documentation
Open: http://localhost:8000/docs

---

## File Structure

```
BandruPay/
├── backend-api/              # FastAPI backend
│   ├── main.py              # Entry point
│   ├── database/            # Database configuration
│   ├── services/            # Business logic
│   ├── requirements.txt      # Python dependencies
│   └── .env                 # Environment variables
│
├── superadmin/              # React admin portal
│   ├── src/                 # React components
│   ├── package.json         # Node dependencies
│   ├── vite.config.js       # Vite configuration
│   └── .env.local           # Frontend env vars
│
├── START.bat                # Windows batch starter
├── START.ps1                # PowerShell starter
├── STARTUP_GUIDE.md         # Detailed setup guide
├── FULL_AUDIT_REPORT.md     # Bug audit report
└── BUG_FIX_SUMMARY.md       # Quick bug fixes summary
```

---

## Important Notes

✅ **All 9 bugs have been fixed** - See FULL_AUDIT_REPORT.md

✅ **Token refresh fixed** - Sessions no longer expire after 30 minutes

✅ **OTP security improved** - Only one valid OTP at a time

✅ **Database transactions safe** - Proper rollback on errors

✅ **Financial precision** - All amounts use Decimal type

✅ **Code quality** - Dead code removed, schemas fixed

---

## Development Tips

### Hot Reload
- **Backend:** Edit Python files → Auto-reloads (reload=True in main.py)
- **Frontend:** Edit React files → Auto-updates in browser

### API Documentation
Navigate to: http://localhost:8000/docs
- Try API endpoints directly from the Swagger UI
- See request/response formats

### Browser DevTools
- Press `F12` to open browser console
- Check Network tab for API calls
- Monitor for 401 (auth errors)

### Backend Logs
Check terminal where you started backend for:
- Database connection status
- API request logs
- Error messages
- OTP generation logs

---

## Next Steps

1. ✅ Run the application (use START.bat or START.ps1)
2. ✅ Login with superadmin credentials
3. ✅ Verify all features work (dashboard, user management, etc.)
4. ✅ Check FULL_AUDIT_REPORT.md for details on fixes
5. ✅ Review API docs at http://localhost:8000/docs

---

## Support & Documentation

- **Full Audit Report:** FULL_AUDIT_REPORT.md (500+ lines, detailed bug analysis)
- **Bug Summary:** BUG_FIX_SUMMARY.md (quick reference)
- **Startup Guide:** STARTUP_GUIDE.md (detailed environment setup)
- **API Docs:** http://localhost:8000/docs (when running)

---

**Status:** ✅ Ready to run  
**Risk Level:** LOW (all critical bugs fixed)  
**Production Ready:** YES (after database setup)

Generated: February 5, 2026
