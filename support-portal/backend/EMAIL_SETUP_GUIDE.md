# Email Notification Setup Guide

## Overview

Users now receive **email notifications** when P1 Critical incidents are created. The email includes:

- **Subject**: "P1 critical has been made"
- **Message**: P1 Critical Title, Description, Username, Client/Merchant

## Email Configuration

### Option 1: Gmail (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Support Portal"
   - Copy the 16-character password

3. **Update .env file**:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Support Portal
```

### Option 2: Office 365 / Outlook

```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-password
FROM_EMAIL=your-email@company.com
FROM_NAME=Support Portal
```

### Option 3: Custom SMTP Server

```bash
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587
SMTP_USER=support@yourdomain.com
SMTP_PASSWORD=your-password
FROM_EMAIL=support@yourdomain.com
FROM_NAME=Support Portal
```

## Email Format

When a user creates a P1 incident, they receive:

### Email Subject:
```
P1 critical has been made
```

### Email Body (HTML):
```
📧 Email-Subject: P1 critical has been made

🚨 P1 Critical Incident Alert
Your critical incident has been logged and our operations team 
has been immediately notified.

🚨 P1 Critical Title:
[Incident Title]

📝 Description:
[Incident Description]

👤 Username:
[User's Name]

🏢 Client/Merchant:
[Client Company Name]

📧 Email:
[User's Email]

────────────────────
Incident ID: P1-XXXXX
Created: 2025-12-02 10:30:00

We will respond to this incident as quickly as possible.
You will receive updates as our team works on resolving this issue.

Thank you,
Support Portal
```

## Testing Email Configuration

Run this test script:

```bash
cd support-portal/backend
python -c "from email_notifier import EmailNotifier; notifier = EmailNotifier(); print('✅ Configured' if notifier.enabled else '❌ Not configured')"
```

## Test Sending Email

Create a test script:

```python
from email_notifier import EmailNotifier

notifier = EmailNotifier()

test_incident = {
    'subject': 'Test P1 Incident',
    'description': 'This is a test incident to verify email notifications',
    'user_name': 'Test User',
    'user_email': 'test@example.com',  # Change to your email
    'merchant_name': 'Test Client',
    'incident_id': 'TEST-001',
    'created_at': '2025-12-02T10:30:00'
}

if notifier.send_p1_notification(test_incident):
    print("✅ Test email sent successfully!")
else:
    print("❌ Failed to send test email")
```

## Troubleshooting

### Issue: Email not sending

**Check:**
1. SMTP credentials are correct in .env
2. App Password is used (not regular password for Gmail)
3. Port 587 is not blocked by firewall
4. SMTP_USER and FROM_EMAIL are set

**Test SMTP connection:**
```python
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print("✅ SMTP connection successful")
server.quit()
```

### Issue: Gmail blocking sign-in

**Solutions:**
- Use App Password (not regular password)
- Enable "Less secure app access" (not recommended)
- Use 2FA + App Password (recommended)

### Issue: Office 365 authentication error

**Solution:**
- Use full email as SMTP_USER
- Ensure account has SMTP auth enabled
- Check Modern Authentication settings

## Email + Slack Notifications

When a P1 incident is created:

1. ✅ **Email sent to user** with incident details
2. ✅ **Slack message posted** to client's channel (or default channel)
3. ✅ **Operations team notified** via @here in Slack

Both notifications happen automatically and include the same information.

## Notification Status

Check notification status in the API response:

```json
{
  "ticket": {...},
  "p1_incident": {...},
  "email_notification": "sent",
  "slack_notification": "sent"
}
```

## Disable Email Notifications

To temporarily disable email notifications, remove or comment out SMTP credentials in .env:

```bash
# SMTP_USER=
# SMTP_PASSWORD=
```

Backend will detect missing credentials and skip email notifications while still sending Slack notifications.

## Summary

✅ Users receive immediate email notification when they create P1 incidents
✅ Email includes all required information (Title, Description, Username, Client)
✅ Professional HTML email format with branding
✅ Works with Gmail, Office 365, and custom SMTP servers
✅ Easy to configure in .env file
✅ Automatic fallback if email fails (Slack still works)
