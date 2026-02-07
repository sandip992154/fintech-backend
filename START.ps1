#!/usr/bin/env pwsh
<#
.SYNOPSIS
BandruPay Application Startup Script
Installs dependencies and starts both frontend and backend servers

.DESCRIPTION
This script will:
1. Verify Python and Node.js are installed
2. Install backend dependencies
3. Install frontend dependencies
4. Start the FastAPI backend server
5. Start the Vite frontend development server
#>

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  BandruPay Application Startup Script" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node.js
Write-Host "[2/5] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    $npmVersion = npm --version 2>&1
    Write-Host "✓ Node.js: $nodeVersion, npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js/npm not found. Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install backend dependencies
Write-Host "`n[3/5] Installing backend dependencies..." -ForegroundColor Yellow
Push-Location "$scriptDir\backend-api"

$packages = @(
    "psycopg2-binary",
    "python-dotenv",
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "pydantic",
    "python-jose",
    "passlib",
    "bcrypt"
)

foreach ($package in $packages) {
    Write-Host "  Installing $package..." -ForegroundColor Gray
    pip install $package --quiet 2>$null
}
Write-Host "✓ Backend dependencies installed" -ForegroundColor Green

Pop-Location

# Install frontend dependencies
Write-Host "[4/5] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location "$scriptDir\superadmin"

if (Test-Path "node_modules") {
    Write-Host "✓ node_modules already exists, skipping npm install" -ForegroundColor Green
} else {
    Write-Host "  Running npm install..." -ForegroundColor Gray
    npm install --silent
    Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
}

Pop-Location

# Start services
Write-Host "`n[5/5] Starting services..." -ForegroundColor Yellow
Write-Host ""

# Start backend
Write-Host "Starting Backend Server (FastAPI)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\backend-api'; python main.py"
Start-Sleep -Seconds 2

# Start frontend
Write-Host "Starting Frontend Server (Vite)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\superadmin'; npm run dev"

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  ✓ Services are starting..." -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Green

Write-Host "Frontend:     http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend:      http://localhost:8000" -ForegroundColor Yellow
Write-Host "API Docs:     http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Default Credentials:" -ForegroundColor Yellow
Write-Host "  Username: superadmin" -ForegroundColor Gray
Write-Host "  Password: SuperAdmin@123" -ForegroundColor Gray
Write-Host ""
Write-Host "Tip: Keep this window open. Services will continue running." -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close this window"
