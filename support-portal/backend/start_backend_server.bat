@echo off
title Support Portal Backend Server
cd /d "c:\Users\fci\support_portal\support-portal\backend"

echo ==========================================
echo   Support Portal API Server
echo ==========================================
echo Starting server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Keep this window open to keep the server running
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

python -m uvicorn simple_app:app --host 0.0.0.0 --port 8000

pause