@echo off
cd /d "%~dp0"
chcp 65001 >nul 2>&1

echo ========================================
echo    AI Agent - Quick Start
echo ========================================
echo.

echo [1/4] Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+
    pause
    exit /b 1
)

echo.
echo [2/4] Installing backend dependencies...
pip install -r backend\requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Installing frontend dependencies...
cd frontend
call npm install --silent 2>nul
cd ..
if errorlevel 1 (
    echo WARNING: Frontend install failed, skipping frontend
)

echo.
echo [4/4] Starting servers...
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

start "Backend" cmd /c "cd backend && python -m uvicorn app.main:app --reload --port 8000 --workers 2"
start "Frontend" cmd /c "cd frontend && npm run dev"

timeout /t 3 >nul
echo.
echo Both servers started!
echo.
pause
