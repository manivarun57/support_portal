@echo off
title Support Portal Frontend Server
cd /d "c:\Users\fci\support_portal\support-portal\frontend"

echo ==========================================
echo   Support Portal Frontend (Next.js)
echo ==========================================
echo Starting development server...
echo Frontend will be available at: http://localhost:3000
echo Backend API: http://localhost:8000
echo.
echo Keep this window open to keep the frontend running
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Use npx instead of npm to avoid PowerShell execution policy issues
npx next dev

pause