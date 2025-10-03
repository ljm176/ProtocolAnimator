@echo off
REM Opentrons Protocol Simulator - Setup Script for Windows

echo.
echo 🔬 Opentrons Protocol Simulator Setup
echo ======================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)

echo ✅ Python found
python --version

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js 16+
    exit /b 1
)

echo ✅ Node.js found
node --version

REM Create virtual environment
echo.
echo 📦 Creating virtual environment (otsimenv)...
if not exist "otsimenv" (
    python -m venv otsimenv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Install Python dependencies
echo.
echo 📦 Installing Python dependencies...
otsimenv\Scripts\pip.exe install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    exit /b 1
)

echo ✅ Python dependencies installed

REM Install Node dependencies
echo.
echo 📦 Installing Node.js dependencies...
npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install Node.js dependencies
    exit /b 1
)

echo ✅ Node.js dependencies installed

REM Create output directory
if not exist "backend\output" mkdir backend\output

echo.
echo ✨ Setup complete!
echo.
echo To run the application:
echo   1. Backend:  npm run server
echo   2. Frontend: npm run dev (in a new terminal)
echo.
echo Access the app at: http://localhost:3000
echo.
echo Note: The backend uses the virtual environment automatically.
echo.
pause
