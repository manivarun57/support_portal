#!/usr/bin/env python3
"""
AWS Lambda Function for P1 Incident Creation and Notification
Handles P1 critical incident creation, Slack notifications, and email alerts
"""

import json
import os
import uuid
import sqlite3
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Environment variables
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_DEFAULT_CHANNEL = os.environ.get('SLACK_CHANNEL_ID')
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/tmp/support_portal.db')
EMAIL_CONSOLE_MODE = os.environ.get('EMAIL_CONSOLE_MODE', 'true').lower() == 'true'
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', SMTP_USER)
FROM_NAME = os.environ.get('FROM_NAME', 'Support Portal')

class P1IncidentHandler:
    """Handles P1 incident creation and notifications"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.slack_bot_token = SLACK_BOT_TOKEN
        self.slack_base_url = "https://slack.com/api"
    
    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_p1_incident(self, ticket_id: str) -> Dict[str, Any]:
        """Create P1 incident record in database"""
        incident_id = f"P1-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()
        
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO p1_incidents (
                    incident_id, ticket_id, created_at, status,
                    slack_notification_sent, email_notification_sent
                )
                VALUES (?, ?, ?, 'active', 0, 0)
            """, (incident_id, ticket_id, created_at))
            conn.commit()
        
        return {
            'incident_id': incident_id,
            'ticket_id': ticket_id,
            'created_at': created_at,
            'status': 'active'
        }
    
    def get_merchant_channel(self, merchant_id: str) -> Optional[str]:
        """Get Slack channel for specific merchant"""
        if not merchant_id:
            return SLACK_DEFAULT_CHANNEL
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT slack_channel_id FROM merchants WHERE merchant_id = ?",
                    (merchant_id,)
                )
                result = cursor.fetchone()
                if result and result[0]:
                    return result[0]
        except Exception as e:
            print(f"⚠️ Error fetching merchant channel: {e}")
        
        return SLACK_DEFAULT_CHANNEL
    
    def post_to_slack(self, incident: Dict[str, Any]) -> Optional[str]:
        """Post P1 incident to Slack channel"""
        if not self.slack_bot_token:
            print("❌ Slack bot token not configured")
            return None
        
        merchant_id = incident.get('merchant_id')
        channel_id = self.get_merchant_channel(merchant_id)
        
        if not channel_id:
            print(f"❌ No Slack channel configured for merchant {merchant_id}")
            return None
        
        # Build Slack message blocks
        incident_id = incident.get('incident_id', 'UNKNOWN')
        subject = incident.get('subject', 'No subject')
        description = incident.get('description', 'No description')
        merchant_name = incident.get('merchant_name', 'Unknown')
        user_name = incident.get('user_name', 'Unknown')
        user_email = incident.get('user_email', '')
        
        message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📧 Email-Subject: P1 critical has been made",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🚨 NEW P1 CRITICAL INCIDENT*\n\nA critical incident has been created and requires immediate attention."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*🚨 P1 Critical Title:*\n{subject}"},
                    {"type": "mrkdwn", "text": f"*🏢 Client/Merchant:*\n{merchant_name}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📝 Description:*\n{description}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*👤 Username:*\n{user_name}"},
                    {"type": "mrkdwn", "text": f"*📧 Email:*\n{user_email}"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*🆔 Incident ID:*\n`{incident_id}`"},
                    {"type": "mrkdwn", "text": f"*📅 Created:*\n{incident.get('created_at', 'N/A')}"}
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Posted from Support Portal | P1 Critical Tracking"
                    }
                ]
            }
        ]
        
        # Post to Slack
        try:
            response = requests.post(
                f"{self.slack_base_url}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.slack_bot_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": channel_id,
                    "blocks": message_blocks,
                    "text": f"🚨 P1 Critical: {subject}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    thread_ts = data.get("ts")
                    print(f"✅ Posted to Slack channel {channel_id} (thread: {thread_ts})")
                    return thread_ts
                else:
                    print(f"❌ Slack API error: {data.get('error')}")
            else:
                print(f"❌ Slack request failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error posting to Slack: {e}")
        
        return None
    
    def send_email_notification(self, incident: Dict[str, Any]) -> bool:
        """Send email notification (console mode or SMTP)"""
        user_email = incident.get('user_email', '')
        if not user_email:
            print("⚠️ No user email provided")
            return False
        
        incident_id = incident.get('incident_id', 'N/A')
        subject = incident.get('subject', 'P1 Critical Incident')
        description = incident.get('description', 'No description')
        merchant_name = incident.get('merchant_name', 'Unknown')
        user_name = incident.get('user_name', 'Unknown')
        
        email_body = f"""
📧 Email-Subject: P1 critical has been made

🚨 P1 Critical Incident Alert
Your critical incident has been logged and our operations team has been immediately notified.

🚨 P1 Critical Title: {subject}
📝 Description: {description}
👤 Username: {user_name}
🏢 Client/Merchant: {merchant_name}
📧 Email: {user_email}

────────────────────
Incident ID: {incident_id}
Created: {incident.get('created_at', 'N/A')}

We will respond to this incident as quickly as possible.
You will receive updates as our team works on resolving this issue.

Thank you,
{FROM_NAME}
"""
        
        # Console mode - just log
        if EMAIL_CONSOLE_MODE:
            print("=" * 70)
            print(f"📧 EMAIL LOGGED - {datetime.now().isoformat()}")
            print("=" * 70)
            print(f"To: {user_email}")
            print(f"Subject: P1 critical has been made")
            print("─" * 70)
            print(email_body)
            print("=" * 70)
            print(f"✅ Email logged (Console Mode) - Recipient: {user_email}")
            return True
        
        # SMTP mode - send actual email
        if SMTP_USER and SMTP_PASSWORD:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                msg = MIMEMultipart()
                msg['Subject'] = "P1 critical has been made"
                msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
                msg['To'] = user_email
                msg.attach(MIMEText(email_body, 'plain'))
                
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
                
                print(f"✅ Email sent to {user_email}")
                return True
            except Exception as e:
                print(f"❌ Failed to send email: {e}")
                return False
        
        print("⚠️ Email not configured (SMTP credentials missing)")
        return False
    
    def update_incident_notifications(self, ticket_id: str, thread_ts: Optional[str], 
                                     slack_sent: bool, email_sent: bool):
        """Update incident record with notification status"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE p1_incidents 
                SET slack_thread_ts = ?,
                    slack_notification_sent = ?,
                    slack_notification_sent_at = ?,
                    email_notification_sent = ?,
                    email_notification_sent_at = ?
                WHERE ticket_id = ?
            """, (
                thread_ts,
                1 if slack_sent else 0,
                datetime.now(timezone.utc).isoformat() if slack_sent else None,
                1 if email_sent else 0,
                datetime.now(timezone.utc).isoformat() if email_sent else None,
                ticket_id
            ))
            conn.commit()


def lambda_handler(event, context):
    """
    AWS Lambda handler for P1 incident creation
    
    Event structure:
    {
        "ticket_id": "TKT-xxxxx",
        "subject": "Critical issue",
        "description": "Description of issue",
        "merchant_id": "merchant_xxxxx",
        "merchant_name": "TechCorp",
        "user_name": "John Doe",
        "user_email": "john@example.com",
        "category": "P1 Critical"
    }
    """
    
    print(f"📥 Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Parse event
        if isinstance(event, str):
            event = json.loads(event)
        
        # Extract ticket data
        ticket_id = event.get('ticket_id')
        if not ticket_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'ticket_id is required'})
            }
        
        # Initialize handler
        handler = P1IncidentHandler(DATABASE_PATH)
        
        # Create P1 incident
        p1_incident = handler.create_p1_incident(ticket_id)
        print(f"🚨 P1 Incident created: {p1_incident['incident_id']}")
        
        # Prepare incident data for notifications
        incident_data = {
            'incident_id': p1_incident['incident_id'],
            'ticket_id': ticket_id,
            'subject': event.get('subject', 'No subject'),
            'description': event.get('description', 'No description'),
            'merchant_id': event.get('merchant_id'),
            'merchant_name': event.get('merchant_name', 'Unknown'),
            'user_name': event.get('user_name', 'Unknown'),
            'user_email': event.get('user_email', ''),
            'category': event.get('category', 'P1 Critical'),
            'created_at': p1_incident['created_at']
        }
        
        # Send notifications
        slack_thread_ts = None
        slack_sent = False
        email_sent = False
        
        # Slack notification
        try:
            slack_thread_ts = handler.post_to_slack(incident_data)
            slack_sent = slack_thread_ts is not None
        except Exception as e:
            print(f"❌ Slack notification error: {e}")
        
        # Email notification
        try:
            email_sent = handler.send_email_notification(incident_data)
        except Exception as e:
            print(f"❌ Email notification error: {e}")
        
        # Update incident with notification status
        handler.update_incident_notifications(
            ticket_id, slack_thread_ts, slack_sent, email_sent
        )
        
        # Return response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'incident_id': p1_incident['incident_id'],
                'ticket_id': ticket_id,
                'slack_notification': 'sent' if slack_sent else 'failed',
                'email_notification': 'sent' if email_sent else 'failed',
                'slack_thread_ts': slack_thread_ts
            })
        }
        
        print(f"✅ P1 incident processed successfully: {p1_incident['incident_id']}")
        return response
        
    except Exception as e:
        print(f"❌ Lambda error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "ticket_id": "TKT-TEST-001",
        "subject": "Critical Database Connection Failure",
        "description": "Production database is not responding. Multiple users unable to access the system.",
        "merchant_id": "merchant_510eaea5f65f",
        "merchant_name": "TechCorp Inc.",
        "user_name": "Dheeraj",
        "user_email": "dheeraj.narayanam@payintelli.com",
        "category": "P1 Critical"
    }
    
    # Mock context
    class MockContext:
        function_name = "p1_incident_handler"
        memory_limit_in_mb = 256
        invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:p1_incident_handler"
        aws_request_id = "test-request-id"
    
    print("🧪 Testing Lambda function locally...")
    print("=" * 70)
    
    result = lambda_handler(test_event, MockContext())
    
    print("\n" + "=" * 70)
    print("📤 Lambda Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
