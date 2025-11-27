@echo off
echo ==========================================
echo   Support Portal Backend Setup & Run
echo ==========================================
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found. Please run this script from the backend directory.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        echo Make sure Python 3.8+ is installed and in your PATH
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip and install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo ✅ Created .env file - you can edit it to customize settings
)

REM Create uploads directory
if not exist "uploads" (
    mkdir uploads
    echo ✅ Created uploads directory
)

echo.
echo ==========================================
echo      Starting Support Portal API
echo ==========================================
echo 📍 Server: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo 💾 Database: SQLite (support_portal.db)
echo 📁 Uploads: uploads/ folder
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Run the application
python app.py

pause