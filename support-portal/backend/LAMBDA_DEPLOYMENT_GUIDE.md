# P1 Incident Lambda Function Deployment Guide

## Overview
This Lambda function handles P1 critical incident creation, Slack notifications, and email alerts.

## Features
- ✅ Creates P1 incident records in database
- ✅ Sends Slack notifications to merchant-specific channels
- ✅ Sends email notifications (console mode or SMTP)
- ✅ Multi-client support with channel routing
- ✅ Updates incident records with notification status

## Prerequisites
1. AWS Account with Lambda access
2. Slack Bot Token with permissions
3. Database (SQLite or RDS)
4. (Optional) SMTP credentials for email

## Deployment Steps

### 1. Prepare Lambda Package
```bash
# Create deployment directory
mkdir lambda_package
cd lambda_package

# Install dependencies
pip install -r lambda_requirements.txt -t .

# Copy Lambda function
cp lambda_p1_incident_handler.py .

# Create deployment ZIP
zip -r p1_incident_lambda.zip .
```

### 2. Create Lambda Function in AWS Console
1. Go to AWS Lambda Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Function name: `p1-incident-handler`
5. Runtime: `Python 3.11`
6. Architecture: `x86_64`
7. Click "Create function"

### 3. Upload Code
1. In the Lambda function page, go to "Code" tab
2. Click "Upload from" → ".zip file"
3. Select `p1_incident_lambda.zip`
4. Click "Save"

### 4. Configure Environment Variables
Go to "Configuration" → "Environment variables" and add:

```
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C0A10UFAT9N
DATABASE_PATH=/tmp/support_portal.db
EMAIL_CONSOLE_MODE=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=dheeraj.narayanam@payintelli.com
SMTP_PASSWORD=
FROM_EMAIL=dheeraj.narayanam@payintelli.com
FROM_NAME=Support Portal
```

### 5. Configure Lambda Settings
**Basic settings:**
- Memory: 256 MB
- Timeout: 30 seconds
- Handler: `lambda_p1_incident_handler.lambda_handler`

**Execution role:**
- Needs permissions for CloudWatch Logs
- If using RDS: VPC access and security group permissions

### 6. Database Setup (Choose One)

**Option A: SQLite (for testing)**
- Database stored in `/tmp/support_portal.db`
- Note: `/tmp` is cleared between invocations
- Good for testing, not production

**Option B: Amazon RDS**
- Create RDS PostgreSQL/MySQL instance
- Update DATABASE_PATH to connection string
- Configure VPC and security groups
- Lambda needs RDS access in same VPC

**Option C: Use existing database**
- Set up Lambda in same VPC as your database
- Update connection string in environment variables

### 7. Test the Lambda Function

**Test Event (JSON):**
```json
{
  "ticket_id": "TKT-TEST-001",
  "subject": "Critical Database Connection Failure",
  "description": "Production database is not responding. Multiple users unable to access the system.",
  "merchant_id": "merchant_510eaea5f65f",
  "merchant_name": "TechCorp Inc.",
  "user_name": "Dheeraj",
  "user_email": "dheeraj.narayanam@payintelli.com",
  "category": "P1 Critical"
}
```

**Click "Test" button**
- Should see "✅ P1 incident processed successfully"
- Check CloudWatch Logs for detailed output
- Verify Slack message posted
- Check email log (console mode)

## Integration with FastAPI Backend

### Option 1: Invoke Lambda from API
```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

# In your create_ticket endpoint:
if ticket_data.priority == 'P1':
    # Invoke Lambda
    response = lambda_client.invoke(
        FunctionName='p1-incident-handler',
        InvocationType='Event',  # Async
        Payload=json.dumps({
            'ticket_id': ticket.id,
            'subject': ticket.subject,
            'description': ticket.description,
            'merchant_id': user_info.get('merchant_id'),
            'merchant_name': user_info.get('merchant_name'),
            'user_name': user_info.get('full_name'),
            'user_email': user_info.get('email'),
            'category': ticket_data.category
        })
    )
```

### Option 2: API Gateway Trigger
1. Create API Gateway REST API
2. Create POST endpoint `/p1-incident`
3. Set Lambda function as integration
4. Deploy API
5. Call from FastAPI:
```python
import requests

response = requests.post(
    'https://your-api-gateway-url/p1-incident',
    json=incident_data
)
```

### Option 3: SNS/SQS Trigger
1. Create SNS topic or SQS queue
2. Set Lambda as subscriber
3. Publish to SNS/SQS from FastAPI
4. Lambda processes asynchronously

## Monitoring

### CloudWatch Logs
- Go to CloudWatch → Log groups
- Find `/aws/lambda/p1-incident-handler`
- View execution logs

### CloudWatch Metrics
- Invocations
- Errors
- Duration
- Throttles

### Alarms
Set up alarms for:
- High error rate
- Long execution time
- Function throttling

## Cost Estimation

**Lambda Pricing (us-east-1):**
- First 1M requests/month: FREE
- After: $0.20 per 1M requests
- Compute: $0.0000166667 per GB-second

**Example:**
- 1000 P1 incidents/month
- 30 seconds each
- 256 MB memory
- Cost: ~$0.13/month

## Security Best Practices

1. **Secrets Management:**
   - Store Slack token in AWS Secrets Manager
   - Store SMTP password in Secrets Manager
   - Update Lambda to fetch from Secrets Manager

2. **IAM Permissions:**
   - Minimal permissions (least privilege)
   - Separate execution role per Lambda

3. **VPC Configuration:**
   - Place Lambda in private subnet
   - Use NAT Gateway for internet access
   - Security groups for database access

4. **Encryption:**
   - Enable encryption at rest
   - Use TLS for all external calls

## Troubleshooting

### "Module not found" error
- Ensure dependencies in lambda_requirements.txt
- Rebuild deployment package
- Check ZIP structure (files at root, not in subfolder)

### Database connection timeout
- Check VPC configuration
- Verify security group rules
- Ensure Lambda in same VPC as database

### Slack notification failed
- Verify SLACK_BOT_TOKEN is correct
- Check bot has `chat:write` permission
- Verify channel ID exists

### Email not sending
- Check SMTP credentials
- Verify SMTP_HOST and SMTP_PORT
- Check firewall/security group allows outbound on port 587

## Local Testing

```bash
# Set environment variables
export SLACK_BOT_TOKEN=xoxb-your-token
export SLACK_CHANNEL_ID=C0A10UFAT9N
export DATABASE_PATH=support_portal.db
export EMAIL_CONSOLE_MODE=true

# Run test
python lambda_p1_incident_handler.py
```

## Production Checklist

- [ ] Lambda function deployed
- [ ] Environment variables configured
- [ ] Database connection working
- [ ] Slack notifications tested
- [ ] Email notifications tested
- [ ] CloudWatch logs enabled
- [ ] CloudWatch alarms set up
- [ ] Secrets moved to Secrets Manager
- [ ] VPC configuration (if needed)
- [ ] API Gateway configured (if using)
- [ ] Integration with FastAPI tested
- [ ] Load testing completed
- [ ] Documentation updated

## Support

For issues:
1. Check CloudWatch Logs
2. Verify environment variables
3. Test with sample event
4. Review execution role permissions
5. Check VPC/security group configuration
