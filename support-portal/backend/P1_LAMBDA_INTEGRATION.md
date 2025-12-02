# Integration Guide: How to use P1 Lambda in app.py

## Step 1: Import the Lambda client at the top of app.py

```python
# Import P1 Lambda client
try:
    from p1_lambda_client import P1LambdaClient
    HAS_P1_LAMBDA_CLIENT = True
except ImportError:
    HAS_P1_LAMBDA_CLIENT = False
    print("⚠️ p1_lambda_client not available")
```

## Step 2: Initialize P1 Lambda client (around line 750 after email_notifier)

```python
# Initialize P1 Lambda Client (for production)
p1_lambda_client = None
if HAS_P1_LAMBDA_CLIENT:
    try:
        p1_lambda_client = P1LambdaClient()
        print("✅ P1 Lambda Client initialized")
    except Exception as e:
        print(f"⚠️ P1 Lambda Client initialization failed: {e}")
```

## Step 3: Replace P1 incident creation logic (around line 1002)

### REPLACE THIS:
```python
if ticket_data.priority == 'P1':
    # Create P1 incident record first
    p1_incident = p1_incident_repo.create_p1_incident(ticket.id)
    print(f"🚨 P1 Incident created: {p1_incident['incident_id']}")
    
    # Prepare incident data for notifications
    ticket_dict = asdict(ticket)
    ticket_dict['incident_id'] = p1_incident['incident_id']
    # ... rest of notification logic
```

### WITH THIS:
```python
if ticket_data.priority == 'P1':
    # Prepare P1 incident data
    p1_data = {
        'client_id': user_info.get('merchant_id', 'unknown'),
        'client_name': user_info.get('merchant_name', 'Unknown'),
        'user_id': user_info.get('user_id', 'unknown'),
        'user_name': user_info.get('full_name', 'Unknown'),
        'user_email': user_info.get('email', ''),
        'ticket_id': ticket.id,
        'subject': ticket_data.subject,
        'description': ticket_data.description,
        'category': ticket_data.category,
        'slack_channel_id': user_info.get('merchant_slack_channel', SLACK_CHANNEL_ID)
    }
    
    # Use Lambda if enabled, otherwise use local processing
    if p1_lambda_client and p1_lambda_client.enabled:
        # Invoke Lambda to handle P1 incident (async - don't wait)
        print("📤 Invoking P1 Lambda function...")
        result = p1_lambda_client.invoke_create_p1_incident(p1_data, async_mode=True)
        if result:
            print(f"✅ P1 Lambda invoked successfully")
            slack_sent = True  # Lambda handles notifications
            email_sent = True
        else:
            print("⚠️ P1 Lambda invocation failed - using local fallback")
            # Fall back to local processing below
    
    if not (p1_lambda_client and p1_lambda_client.enabled):
        # LOCAL FALLBACK: Original P1 processing
        p1_incident = p1_incident_repo.create_p1_incident(ticket.id)
        print(f"🚨 P1 Incident created locally: {p1_incident['incident_id']}")
        
        # Original Slack/Email notification logic
        ticket_dict = asdict(ticket)
        ticket_dict['incident_id'] = p1_incident['incident_id']
        ticket_dict['merchant_id'] = user_info.get('merchant_id', None)
        # ... rest of your existing notification code
```

## Step 4: Environment Variables

Add to your .env file:

```bash
# P1 Lambda Configuration
USE_P1_LAMBDA=true                          # Enable Lambda integration
P1_LAMBDA_FUNCTION_NAME=P1IncidentHandler   # Lambda function name
DYNAMODB_P1_TABLE=P1Incidents               # DynamoDB table name

# AWS Credentials (if not using IAM roles)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

## Benefits:

✅ **Async Processing**: Main app doesn't wait for Slack/email
✅ **Scalable**: Lambda auto-scales with P1 incident load
✅ **DynamoDB**: Multi-tenant storage, better than SQLite
✅ **Fallback**: If Lambda fails, uses local processing
✅ **No Changes to Frontend**: Works transparently

## Testing:

1. **Local mode** (USE_P1_LAMBDA=false): Uses SQLite + local notifications
2. **Lambda mode** (USE_P1_LAMBDA=true): Calls Lambda → DynamoDB
