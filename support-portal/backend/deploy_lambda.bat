@echo off
REM Deployment script for P1 Incident Lambda Function

echo ========================================
echo P1 Incident Lambda Deployment
echo ========================================

REM Create deployment directory
echo.
echo [1/5] Creating deployment directory...
if exist lambda_package rmdir /s /q lambda_package
mkdir lambda_package
cd lambda_package

REM Install dependencies
echo.
echo [2/5] Installing dependencies...
pip install -r ..\lambda_requirements.txt -t .

REM Copy Lambda function
echo.
echo [3/5] Copying Lambda function...
copy ..\lambda_p1_incident_handler.py .

REM Copy shared utilities if needed
if exist ..\shared.py copy ..\shared.py .

REM Create deployment ZIP
echo.
echo [4/5] Creating deployment package...
if exist p1_incident_lambda.zip del p1_incident_lambda.zip
powershell -command "Compress-Archive -Path * -DestinationPath p1_incident_lambda.zip"

echo.
echo [5/5] Deployment package created!
echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Deployment package: lambda_package\p1_incident_lambda.zip
echo Size: 
dir p1_incident_lambda.zip | find "p1_incident_lambda.zip"
echo.
echo Next steps:
echo 1. Go to AWS Lambda Console
echo 2. Create or update function 'p1-incident-handler'
echo 3. Upload p1_incident_lambda.zip
echo 4. Configure environment variables (see LAMBDA_DEPLOYMENT_GUIDE.md)
echo 5. Test with sample event
echo.

pause
