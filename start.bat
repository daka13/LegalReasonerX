@echo off
REM LegalReasonerX Web Application Startup Script for Windows

echo 🚀 Starting LegalReasonerX Web Application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing dependencies...
    pip install -r requirements-web.txt
    echo ✅ Dependencies installed!
    echo.
)

REM Start the application
echo 🌐 Starting server on http://localhost:8000
echo 📚 API documentation available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

pause
