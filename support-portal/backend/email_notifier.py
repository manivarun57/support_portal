#!/usr/bin/env python3
"""
Email Notification Service for P1 Critical Incidents
Sends email notifications to users when P1 incidents are created or updated
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional

class EmailNotifier:
    """Handles email notifications for P1 Critical incidents"""
    
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'Support Portal')
        
        # Console mode - always enabled, logs emails instead of sending
        self.console_mode = os.getenv('EMAIL_CONSOLE_MODE', 'true').lower() == 'true'
        self.log_file = os.getenv('EMAIL_LOG_FILE', 'email_notifications.log')
        
        # Check if email is configured
        self.enabled = self.console_mode or bool(self.smtp_user and self.smtp_password)
        
        if self.console_mode:
            print("📧 Email notifications in CONSOLE MODE - emails will be logged, not sent")
        elif not self.enabled:
            print("⚠️ Email notifications disabled - SMTP credentials not configured")
    
    def send_p1_notification(self, incident: Dict[str, Any]) -> bool:
        """
        Send P1 Critical incident notification email to user
        
        Args:
            incident: Dictionary containing incident details
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            print("⚠️ Email notifications disabled")
            return False
        
        try:
            # Extract incident details
            user_email = incident.get('user_email', '')
            user_name = incident.get('user_name', 'User')
            subject_title = incident.get('subject', 'P1 Critical Incident')
            description = incident.get('description', 'No description provided')
            merchant_name = incident.get('merchant_name', 'Unknown')
            incident_id = incident.get('incident_id', 'N/A')
            created_at = incident.get('created_at', datetime.now().isoformat())
            
            if not user_email:
                print("⚠️ No user email provided")
                return False
            
            # Console mode - log instead of sending
            if self.console_mode:
                return self._log_email(
                    to=user_email,
                    subject="P1 critical has been made",
                    body=f"""
📧 Email-Subject: P1 critical has been made

🚨 P1 Critical Incident Alert
Your critical incident has been logged and our operations team has been immediately notified.

🚨 P1 Critical Title: {subject_title}
📝 Description: {description}
👤 Username: {user_name}
🏢 Client/Merchant: {merchant_name}
📧 Email: {user_email}

────────────────────
Incident ID: {incident_id}
Created: {created_at}

We will respond to this incident as quickly as possible.
You will receive updates as our team works on resolving this issue.

Thank you,
{self.from_name}
"""
                )
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "P1 critical has been made"
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = user_email
            
            # Plain text version
            text_body = f"""
P1 Critical Incident Created

Email-Subject: P1 critical has been made

Message:
--------
P1 Critical Title: {subject_title}

Description: {description}

Username: {user_name}
Client/Merchant: {merchant_name}

--------
Incident Details:
Incident ID: {incident_id}
Created: {created_at}

Your P1 Critical incident has been logged and our operations team has been notified.
We will respond to this incident as quickly as possible.

Thank you,
{self.from_name}
"""
            
            # HTML version
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc3545; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
        .field {{ margin: 15px 0; padding: 10px; background-color: white; border-left: 4px solid #dc3545; }}
        .field-label {{ font-weight: bold; color: #dc3545; }}
        .footer {{ background-color: #e9ecef; padding: 15px; text-align: center; border-radius: 0 0 5px 5px; font-size: 12px; }}
        .alert {{ background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📧 Email-Subject: P1 critical has been made</h2>
        </div>
        
        <div class="content">
            <div class="alert">
                <strong>🚨 P1 Critical Incident Alert</strong><br>
                Your critical incident has been logged and our operations team has been immediately notified.
            </div>
            
            <div class="field">
                <div class="field-label">🚨 P1 Critical Title:</div>
                <div>{subject_title}</div>
            </div>
            
            <div class="field">
                <div class="field-label">📝 Description:</div>
                <div>{description}</div>
            </div>
            
            <div class="field">
                <div class="field-label">👤 Username:</div>
                <div>{user_name}</div>
            </div>
            
            <div class="field">
                <div class="field-label">🏢 Client/Merchant:</div>
                <div>{merchant_name}</div>
            </div>
            
            <div class="field">
                <div class="field-label">📧 Email:</div>
                <div>{user_email}</div>
            </div>
            
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #dee2e6;">
            
            <p><strong>Incident ID:</strong> {incident_id}</p>
            <p><strong>Created:</strong> {created_at}</p>
            
            <p style="margin-top: 20px;">
                We will respond to this incident as quickly as possible. 
                You will receive updates as our team works on resolving this issue.
            </p>
        </div>
        
        <div class="footer">
            Thank you,<br>
            <strong>{self.from_name}</strong>
        </div>
    </div>
</body>
</html>
"""
            
            # Attach both versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ P1 notification email sent to {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email notification: {e}")
            return False
    
    def _log_email(self, to: str, subject: str, body: str) -> bool:
        """Log email to console and file instead of sending"""
        try:
            log_entry = f"""
{'='*70}
📧 EMAIL LOGGED - {datetime.now().isoformat()}
{'='*70}
To: {to}
Subject: {subject}
{'─'*70}
{body}
{'='*70}
"""
            # Print to console
            print(log_entry)
            
            # Append to log file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
            
            print(f"✅ Email logged successfully (Console Mode) - Recipient: {to}")
            return True
        except Exception as e:
            print(f"❌ Failed to log email: {e}")
            return False
    
    def send_p1_update(self, incident: Dict[str, Any], update_message: str) -> bool:
        """
        Send P1 incident update email to user
        
        Args:
            incident: Dictionary containing incident details
            update_message: Update message to send
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            user_email = incident.get('user_email', '')
            user_name = incident.get('user_name', 'User')
            subject_title = incident.get('subject', 'P1 Critical Incident')
            incident_id = incident.get('incident_id', 'N/A')
            
            if not user_email:
                return False
            
            # Console mode - log instead of sending
            if self.console_mode:
                return self._log_email(
                    to=user_email,
                    subject=f"P1 Incident Update - {subject_title}",
                    body=f"""
💬 P1 Critical Incident Update

Incident ID: {incident_id}
Title: {subject_title}

Update:
{update_message}

Thank you,
{self.from_name}
"""
                )
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"P1 Incident Update - {subject_title}"
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = user_email
            
            text_body = f"""
P1 Critical Incident Update

Incident ID: {incident_id}
Title: {subject_title}

Update:
{update_message}

Thank you,
{self.from_name}
"""
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0d6efd; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
        .update {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #0d6efd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>💬 P1 Incident Update</h2>
        </div>
        <div class="content">
            <p><strong>Incident ID:</strong> {incident_id}</p>
            <p><strong>Title:</strong> {subject_title}</p>
            <div class="update">
                <strong>Update:</strong><br>
                {update_message}
            </div>
        </div>
    </div>
</body>
</html>
"""
            
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ P1 update email sent to {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send update email: {e}")
            return False


# Configuration instructions
EMAIL_SETUP_INSTRUCTIONS = """
=============================================================================
EMAIL NOTIFICATION SETUP
=============================================================================

Add these to your .env file:

# Email Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Support Portal

For Gmail:
1. Enable 2-factor authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the App Password as SMTP_PASSWORD

For other email providers:
- Office 365: smtp.office365.com (port 587)
- Outlook: smtp-mail.outlook.com (port 587)
- Yahoo: smtp.mail.yahoo.com (port 587)

=============================================================================
"""

if __name__ == "__main__":
    print(EMAIL_SETUP_INSTRUCTIONS)
