@echo off
echo ==========================================
echo   Support Portal Backend - Simple Version
echo ==========================================
echo.

REM Check if we're in the backend directory
if not exist "simple_app.py" (
    echo Error: simple_app.py not found. Please run from backend directory.
    pause
    exit /b 1
)

REM Create .env if needed
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo ✅ Created .env file
    )
)

REM Create uploads directory
if not exist "uploads" (
    mkdir uploads
    echo ✅ Created uploads directory
)

echo Starting server...
echo.
echo ==========================================
echo      Support Portal API Server
echo ==========================================
echo 📍 Server: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs  
echo 💾 Database: SQLite (support_portal.db)
echo 📁 Uploads: uploads/ folder
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Start the server using uvicorn directly
python -m uvicorn simple_app:app --host 0.0.0.0 --port 8000 --reload

pause