@echo off
REM Quick Test Script for Authentication System
echo ========================================
echo  Support Portal Authentication Test
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Creating test merchants and users...
echo.
python create_test_users.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to create test data!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Test Data Created Successfully!
echo ========================================
echo.
echo Test Login Credentials:
echo.
echo Merchant: TechCorp
echo   - john.doe / password123 (admin)
echo   - sarah.smith / password123 (user)
echo   - mike.johnson / password123 (user)
echo.
echo Merchant: ShopifyPlus
echo   - alice.wong / password123 (admin)
echo   - bob.martin / password123 (user)
echo.
echo Merchant: FinanceOne
echo   - emma.davis / password123 (admin)
echo.
echo ========================================
echo  Next Steps:
echo ========================================
echo 1. Backend should be running on http://localhost:8000
echo 2. Frontend should be running on http://localhost:3000
echo 3. Use test_api.py to test authentication
echo.
pause
