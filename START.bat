@echo off
REM BandruPay Startup Script for Windows
REM This script installs dependencies and starts both frontend and backend

echo.
echo ============================================
echo   BandruPay Application Startup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [1/5] Python found: 
python --version

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js and npm.
    pause
    exit /b 1
)

echo [2/5] Node.js found:
node --version

REM Install backend dependencies
echo.
echo [3/5] Installing backend dependencies...
cd /d "%~dp0backend-api"
pip install psycopg2-binary python-dotenv fastapi uvicorn sqlalchemy pydantic python-jose passlib bcrypt --quiet
if errorlevel 1 (
    echo WARNING: Backend dependency installation had issues. Continuing anyway...
)

REM Install frontend dependencies
echo [4/5] Installing frontend dependencies...
cd /d "%~dp0superadmin"
if exist node_modules (
    echo Skipping npm install (node_modules already exists)
) else (
    call npm install --silent
)

REM Start servers
echo.
echo [5/5] Starting servers...
echo.
echo ============================================
echo   Starting Backend (FastAPI on port 8000)
echo ============================================
cd /d "%~dp0backend-api"
start "BandruPay Backend" python main.py

timeout /t 3 /nobreak

echo.
echo ============================================
echo   Starting Frontend (Vite on port 5173)
echo ============================================
cd /d "%~dp0superadmin"
start "BandruPay Frontend" npm run dev

echo.
echo ============================================
echo   Services Starting...
echo ============================================
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Default Login:
echo   Username: superadmin
echo   Password: SuperAdmin@123
echo.
echo Press any key to close this window...
echo (The services will continue running)
pause
