# ⚡ QUICK START - One Page

## START YOUR APP NOW

### Windows Users: Click this file
```
START.bat
```

### Mac/Linux or Manual Start

**Terminal 1 - Backend:**
```bash
cd backend-api
pip install psycopg2-binary python-dotenv fastapi uvicorn sqlalchemy pydantic python-jose passlib bcrypt
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd superadmin
npm install
npm run dev
```

---

## OPEN YOUR BROWSER

| What | URL | Purpose |
|------|-----|---------|
| **Admin Panel** | http://localhost:5173 | Main application |
| **API Docs** | http://localhost:8000/docs | Test API endpoints |

---

## LOGIN

```
Username: superadmin
Password: SuperAdmin@123
```

Then enter the OTP sent to email.

---

## KEY INFORMATION

| Item | Details |
|------|---------|
| **Backend** | Port 8000 (FastAPI) |
| **Frontend** | Port 5173 (React + Vite) |
| **Database** | Cloud PostgreSQL (Render) |
| **Auto-reload** | ✓ Enabled for both |

---

## WHAT'S BEEN FIXED

✅ **10 bugs identified and fixed**
- Token expiry (30 days → 30 minutes)
- Session auto-refresh
- OTP security
- Transaction safety
- Database integrity
- Code quality

See `FULL_AUDIT_REPORT.md` for details.

---

## COMMON ISSUES

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `taskkill /PID <PID> /F` (Windows) |
| psycopg2 error | `pip install psycopg2-binary` |
| npm fails | `rm -r node_modules` then `npm install` |
| Database error | Verify internet (cloud DB) |

---

## DOCUMENTATION

| File | Contents |
|------|----------|
| `FULL_AUDIT_REPORT.md` | 500+ line detailed bug analysis |
| `BUG_FIX_SUMMARY.md` | Quick bug reference |
| `STARTUP_GUIDE.md` | Full setup guide |
| `README_STARTUP.md` | Troubleshooting |

---

## STATUS

✅ Ready to run  
✅ All bugs fixed  
✅ Production ready  

**That's it! Start your app now. 🚀**
