#!/usr/bin/env python3
"""
AWS Lambda Function for P1 Incident Management
Multi-tenant architecture with DynamoDB storage

This Lambda function handles:
1. Creating P1 incidents in DynamoDB
2. Sending Slack notifications to client-specific channels
3. Sending email notifications to users
4. Storing all incident data for multiple clients

Trigger: API Gateway or direct invocation from main application
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# AWS imports
import boto3
from boto3.dynamodb.conditions import Key, Attr

# Slack/Email imports
import requests


class P1LambdaHandler:
    """Handles P1 incident creation and notifications in AWS Lambda environment"""
    
    def __init__(self):
        # DynamoDB setup
        self.dynamodb = boto3.resource('dynamodb',
            region_name=os.environ.get('AWS_REGION', 'ap-south-1')
        )
        self.table_name = os.environ.get('DYNAMODB_P1_TABLE', 'P1Incidents')
        self.table = self.dynamodb.Table(self.table_name)
        
        # Slack configuration
        self.slack_bot_token = os.environ.get('SLACK_BOT_TOKEN', '')
        self.slack_api_base = "https://slack.com/api"
        
        # Email configuration (console mode for now)
        self.email_console_mode = os.environ.get('EMAIL_CONSOLE_MODE', 'true').lower() == 'true'
        
        print(f"✅ P1 Lambda Handler initialized - Table: {self.table_name}")
    
    def generate_incident_id(self) -> str:
        """Generate unique P1 incident ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:8]
        return f"P1-{timestamp}-{random_suffix}"
    
    def create_p1_incident(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create P1 incident in DynamoDB
        
        Args:
            event_data: {
                'client_id': 'merchant_xxx',
                'client_name': 'TechCorp Inc.',
                'user_id': 'user_xxx',
                'user_name': 'John Doe',
                'user_email': 'john@techcorp.com',
                'ticket_id': 'TKT-xxx',
                'subject': 'Critical Database Failure',
                'description': 'Production database not responding...',
                'category': 'Infrastructure',
                'priority': 'P1',
                'slack_channel_id': 'C0A10UFAT9N'  # Client-specific channel
            }
        
        Returns:
            {
                'success': True,
                'incident_id': 'P1-xxx',
                'slack_sent': True,
                'email_sent': True
            }
        """
        try:
            # Generate incident ID
            incident_id = self.generate_incident_id()
            timestamp = datetime.utcnow().isoformat()
            
            # Prepare incident item
            incident_item = {
                # Primary Keys (for multi-tenant partitioning)
                'client_id': event_data['client_id'],
                'incident_id': incident_id,
                
                # Client/Merchant Info
                'client_name': event_data.get('client_name', 'Unknown'),
                
                # User Info
                'user_id': event_data['user_id'],
                'user_name': event_data.get('user_name', 'Unknown'),
                'user_email': event_data.get('user_email', ''),
                
                # Ticket Info
                'ticket_id': event_data['ticket_id'],
                'subject': event_data['subject'],
                'description': event_data['description'],
                'category': event_data.get('category', 'General'),
                'priority': 'P1',
                
                # Slack Integration
                'slack_channel_id': event_data.get('slack_channel_id', ''),
                'slack_thread_ts': '',
                'slack_notification_sent': False,
                'slack_notification_sent_at': None,
                
                # Email Notification
                'email_notification_sent': False,
                'email_notification_sent_at': None,
                
                # Status
                'status': 'active',
                'created_at': timestamp,
                'updated_at': timestamp,
                'resolved_at': None,
                
                # Message history
                'slack_messages': []
            }
            
            # Store in DynamoDB
            self.table.put_item(Item=incident_item)
            print(f"✅ P1 Incident created in DynamoDB: {incident_id}")
            
            # Send Slack notification
            slack_sent = False
            thread_ts = None
            if self.slack_bot_token and incident_item['slack_channel_id']:
                slack_result = self.send_slack_notification(incident_item)
                if slack_result:
                    slack_sent = True
                    thread_ts = slack_result.get('thread_ts')
                    
                    # Update DynamoDB with Slack thread info
                    self.update_slack_thread(
                        event_data['client_id'],
                        incident_id,
                        thread_ts
                    )
            
            # Send Email notification
            email_sent = False
            if incident_item['user_email']:
                email_sent = self.send_email_notification(incident_item)
            
            return {
                'success': True,
                'incident_id': incident_id,
                'client_id': event_data['client_id'],
                'slack_sent': slack_sent,
                'slack_thread_ts': thread_ts,
                'email_sent': email_sent,
                'created_at': timestamp
            }
            
        except Exception as e:
            print(f"❌ Error creating P1 incident: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_slack_notification(self, incident: Dict[str, Any]) -> Optional[Dict]:
        """
        Send P1 incident to Slack channel
        
        Returns:
            {'thread_ts': '1234567890.123456', 'channel': 'C0A10UFAT9N'}
        """
        try:
            # Build Slack message blocks
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
                        "text": f"*🚨 P1 CRITICAL INCIDENT*\n\nA new critical incident has been created and requires immediate attention."
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*🚨 P1 Critical Title:*\n{incident['subject']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🏢 Client/Merchant:*\n{incident['client_name']}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📝 Description:*\n{incident['description']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*👤 Username:*\n{incident['user_name']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*📧 Email:*\n{incident['user_email']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🆔 Incident ID:*\n{incident['incident_id']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🎫 Ticket ID:*\n{incident['ticket_id']}"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"⏰ Created: {incident['created_at']} | 🔴 Status: Active | ⚠️ Priority: P1 Critical"
                        }
                    ]
                }
            ]
            
            # Post to Slack
            response = requests.post(
                f"{self.slack_api_base}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.slack_bot_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": incident['slack_channel_id'],
                    "blocks": message_blocks,
                    "text": f"🚨 P1 Critical: {incident['subject']}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    thread_ts = data['ts']
                    print(f"✅ Slack notification sent - Thread: {thread_ts}")
                    return {
                        'thread_ts': thread_ts,
                        'channel': incident['slack_channel_id']
                    }
            
            print(f"❌ Slack notification failed: {response.text}")
            return None
            
        except Exception as e:
            print(f"❌ Error sending Slack notification: {e}")
            return None
    
    def send_email_notification(self, incident: Dict[str, Any]) -> bool:
        """
        Send email notification to user (console mode for now)
        """
        try:
            if self.email_console_mode:
                # Log email to console/CloudWatch
                email_content = f"""
{'='*70}
📧 EMAIL NOTIFICATION (Console Mode)
{'='*70}
To: {incident['user_email']}
Subject: P1 critical has been made
{'─'*70}

📧 Email-Subject: P1 critical has been made

🚨 P1 Critical Incident Alert
Your critical incident has been logged and our operations team has been immediately notified.

🚨 P1 Critical Title: {incident['subject']}
📝 Description: {incident['description']}
👤 Username: {incident['user_name']}
🏢 Client/Merchant: {incident['client_name']}
📧 Email: {incident['user_email']}

────────────────────
Incident ID: {incident['incident_id']}
Created: {incident['created_at']}

We will respond to this incident as quickly as possible.
You will receive updates as our team works on resolving this issue.

Thank you,
Support Portal
{'='*70}
"""
                print(email_content)
                return True
            else:
                # TODO: Implement actual email sending via SES
                print("⚠️ Email sending not implemented yet")
                return False
                
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def update_slack_thread(self, client_id: str, incident_id: str, thread_ts: str) -> bool:
        """Update incident with Slack thread timestamp"""
        try:
            self.table.update_item(
                Key={
                    'client_id': client_id,
                    'incident_id': incident_id
                },
                UpdateExpression='SET slack_thread_ts = :thread_ts, slack_notification_sent = :sent, slack_notification_sent_at = :sent_at, updated_at = :updated',
                ExpressionAttributeValues={
                    ':thread_ts': thread_ts,
                    ':sent': True,
                    ':sent_at': datetime.utcnow().isoformat(),
                    ':updated': datetime.utcnow().isoformat()
                }
            )
            print(f"✅ Slack thread updated in DynamoDB")
            return True
        except Exception as e:
            print(f"❌ Failed to update Slack thread: {e}")
            return False
    
    def get_incident(self, client_id: str, incident_id: str) -> Optional[Dict]:
        """Get incident from DynamoDB"""
        try:
            response = self.table.get_item(
                Key={
                    'client_id': client_id,
                    'incident_id': incident_id
                }
            )
            return response.get('Item')
        except Exception as e:
            print(f"❌ Error getting incident: {e}")
            return None
    
    def update_incident_status(self, client_id: str, incident_id: str, status: str) -> bool:
        """Update incident status (active/resolved)"""
        try:
            timestamp = datetime.utcnow().isoformat()
            
            update_expr = 'SET #status = :status, updated_at = :updated'
            expr_values = {
                ':status': status,
                ':updated': timestamp
            }
            
            if status == 'resolved':
                update_expr += ', resolved_at = :resolved'
                expr_values[':resolved'] = timestamp
            
            self.table.update_item(
                Key={
                    'client_id': client_id,
                    'incident_id': incident_id
                },
                UpdateExpression=update_expr,
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues=expr_values
            )
            
            print(f"✅ Incident status updated to: {status}")
            return True
        except Exception as e:
            print(f"❌ Failed to update status: {e}")
            return False


    def get_active_incidents(self, client_id: str = None) -> list:
        """Get all active P1 incidents, optionally filtered by client"""
        try:
            if client_id:
                # Get active incidents for specific client
                response = self.table.query(
                    KeyConditionExpression=Key('client_id').eq(client_id),
                    FilterExpression=Attr('status').eq('active')
                )
            else:
                # Get all active incidents across all clients
                response = self.table.scan(
                    FilterExpression=Attr('status').eq('active')
                )
            
            return response.get('Items', [])
        except Exception as e:
            print(f"❌ Error getting active incidents: {e}")
            return []
    
    def add_comment_to_incident(self, client_id: str, incident_id: str, comment: Dict[str, Any]) -> bool:
        """Add a comment/update to the incident"""
        try:
            comment_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user': comment.get('user', 'System'),
                'message': comment.get('message', ''),
                'type': comment.get('type', 'comment')  # comment, status_update, slack_message
            }
            
            self.table.update_item(
                Key={
                    'client_id': client_id,
                    'incident_id': incident_id
                },
                UpdateExpression='SET slack_messages = list_append(if_not_exists(slack_messages, :empty_list), :new_message), updated_at = :updated',
                ExpressionAttributeValues={
                    ':new_message': [comment_entry],
                    ':empty_list': [],
                    ':updated': datetime.utcnow().isoformat()
                }
            )
            print(f"✅ Comment added to incident {incident_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to add comment: {e}")
            return False


def lambda_handler(event, context):
    """
    AWS Lambda entry point - Complete P1 Incident Handler
    
    Supported Actions:
    
    1. create_p1_incident - Create new P1 incident with notifications
    2. get_incident - Get incident details
    3. update_status - Update incident status (active/resolved)
    4. get_active_incidents - Get all active incidents
    5. add_comment - Add comment/update to incident
    
    Event format examples:
    
    CREATE P1 INCIDENT:
    {
        "action": "create_p1_incident",
        "data": {
            "client_id": "merchant_510eaea5f65f",
            "client_name": "TechCorp Inc.",
            "user_id": "user_xxx",
            "user_name": "John Doe",
            "user_email": "john@techcorp.com",
            "ticket_id": "TKT-xxx",
            "subject": "Critical Database Failure",
            "description": "Production database not responding...",
            "category": "Infrastructure",
            "slack_channel_id": "C0A10UFAT9N"
        }
    }
    
    GET INCIDENT:
    {
        "action": "get_incident",
        "data": {
            "client_id": "merchant_510eaea5f65f",
            "incident_id": "P1-20251202113045-abc123ef"
        }
    }
    
    UPDATE STATUS:
    {
        "action": "update_status",
        "data": {
            "client_id": "merchant_510eaea5f65f",
            "incident_id": "P1-20251202113045-abc123ef",
            "status": "resolved"
        }
    }
    
    GET ACTIVE INCIDENTS:
    {
        "action": "get_active_incidents",
        "data": {
            "client_id": "merchant_510eaea5f65f"  # Optional - omit for all clients
        }
    }
    
    ADD COMMENT:
    {
        "action": "add_comment",
        "data": {
            "client_id": "merchant_510eaea5f65f",
            "incident_id": "P1-20251202113045-abc123ef",
            "comment": {
                "user": "John Doe",
                "message": "Working on database connection issue",
                "type": "comment"
            }
        }
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": True,
            "incident_id": "P1-xxx",
            "data": {...}
        }
    }
    """
    
    print(f"📥 Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Initialize handler
        handler = P1LambdaHandler()
        
        # Parse action
        action = event.get('action', 'create_p1_incident')
        data = event.get('data', {})
        
        if action == 'create_p1_incident':
            # Create P1 incident with notifications
            result = handler.create_p1_incident(data)
            
            return {
                'statusCode': 200 if result.get('success') else 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        elif action == 'get_incident':
            # Get incident details
            client_id = data.get('client_id')
            incident_id = data.get('incident_id')
            
            incident = handler.get_incident(client_id, incident_id)
            
            return {
                'statusCode': 200 if incident else 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': bool(incident),
                    'incident': incident
                })
            }
        
        elif action == 'update_status':
            # Update incident status
            client_id = data.get('client_id')
            incident_id = data.get('incident_id')
            status = data.get('status', 'resolved')
            
            success = handler.update_incident_status(client_id, incident_id, status)
            
            return {
                'statusCode': 200 if success else 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': success,
                    'message': f'Status updated to {status}'
                })
            }
        
        elif action == 'get_active_incidents':
            # Get all active incidents
            client_id = data.get('client_id')  # Optional
            
            incidents = handler.get_active_incidents(client_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'count': len(incidents),
                    'incidents': incidents
                })
            }
        
        elif action == 'add_comment':
            # Add comment to incident
            client_id = data.get('client_id')
            incident_id = data.get('incident_id')
            comment = data.get('comment', {})
            
            success = handler.add_comment_to_incident(client_id, incident_id, comment)
            
            return {
                'statusCode': 200 if success else 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': success,
                    'message': 'Comment added successfully' if success else 'Failed to add comment'
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Unknown action: {action}',
                    'supported_actions': [
                        'create_p1_incident',
                        'get_incident',
                        'update_status',
                        'get_active_incidents',
                        'add_comment'
                    ]
                })
            }
    
    except Exception as e:
        print(f"❌ Lambda error: {e}")
        import traceback
        print(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "action": "create_p1_incident",
        "data": {
            "client_id": "merchant_510eaea5f65f",
            "client_name": "TechCorp Inc.",
            "user_id": "user_aaa4ef7e984f",
            "user_name": "Dheeraj",
            "user_email": "dheeraj.narayanam@payintelli.com",
            "ticket_id": "TKT-test-001",
            "subject": "Critical Database Connection Failure",
            "description": "Production database is not responding. Multiple users unable to access the system. Immediate attention required.",
            "category": "Infrastructure",
            "slack_channel_id": os.getenv('SLACK_CHANNEL_ID', 'C0A10UFAT9N')
        }
    }
    
    print("=" * 70)
    print("LOCAL LAMBDA TEST")
    print("=" * 70)
    
    result = lambda_handler(test_event, None)
    
    print("\n" + "=" * 70)
    print("LAMBDA RESULT")
    print("=" * 70)
    print(json.dumps(json.loads(result['body']), indent=2))
