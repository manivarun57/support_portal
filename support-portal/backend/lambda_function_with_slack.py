"""
Support Portal API - AWS Lambda Function with Slack Integration
Complete FastAPI application optimized for AWS Lambda + P1 Critical Slack Alerts

Instructions:
1. Copy this entire file content
2. Go to AWS Lambda Console
3. Create new function (Python 3.11 runtime)
4. Paste this code in the code editor
5. Set handler to: lambda_function.lambda_handler
6. Deploy and test

Environment Variables to set in Lambda:
- S3_BUCKET_NAME: your-bucket-name (optional)
- DATABASE_URL: postgresql://... (if using RDS, optional)
- DEBUG: false
- SLACK_WEBHOOK_URL: https://hooks.slack.com/services/... (optional, hardcoded below)
"""

import json
import os
import uuid
import base64
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import urllib.parse

# Lambda response helper
def create_response(status_code: int, body: dict, headers: dict = None):
    """Create properly formatted Lambda response"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-User-Id'
    }
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': default_headers
    }

def create_error_response(message: str, status_code: int = 400):
    """Create error response"""
    return create_response(status_code, {
        'success': False,
        'message': message,
        'error_code': status_code
    })

# Slack notification handler
class SlackNotifier:
    def __init__(self):
        # Your Slack webhook URL
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
    
    def send_p1_notification(self, ticket):
        """Send P1 Critical incident notification to Slack"""
        try:
            import urllib.request
            
            # Create rich Slack message for P1 Critical
            message = {
                "text": "🚨 P1 CRITICAL INCIDENT ALERT 🚨",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 P1 CRITICAL INCIDENT ALERT 🚨"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Incident:* {ticket['subject']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Priority:* 🔴 P1 CRITICAL"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Ticket ID:* {ticket['id'][:8]}..."
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Reporter:* {ticket['user_id']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Category:* {ticket['category']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:* {ticket['created_at']}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Description:*\n{ticket['description'][:500]}{'...' if len(ticket['description']) > 500 else ''}"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "⚡ *IMMEDIATE ACTION REQUIRED* - This is a production-critical incident requiring immediate response from the operations team."
                            }
                        ]
                    }
                ]
            }
            
            # Add attachment info if present
            if ticket.get('attachment_url'):
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📎 *Attachment:* <{ticket['attachment_url']}|View File>"
                    }
                })
            
            # Send to Slack
            data = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    print("✅ P1 Critical alert sent to Slack successfully")
                    return True
                else:
                    print(f"❌ Slack notification failed: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Slack notification error: {str(e)}")
            return False
    
    def send_general_notification(self, ticket):
        """Send general ticket notification to Slack (optional for non-P1)"""
        try:
            import urllib.request
            
            priority_emoji = {
                'low': '🟢',
                'medium': '🟡', 
                'high': '🔴',
                'P1': '🚨'
            }
            
            message = {
                "text": f"New support ticket: {ticket['subject']}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{priority_emoji.get(ticket['priority'], '📝')} *New Ticket:* {ticket['subject']}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Priority:* {ticket['priority'].upper()}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Category:* {ticket['category']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Reporter:* {ticket['user_id']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*ID:* {ticket['id'][:8]}..."
                            }
                        ]
                    }
                ]
            }
            
            data = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                return response.status == 200
                
        except Exception as e:
            print(f"Slack notification error: {str(e)}")
            return False

# Database Manager for Lambda
class LambdaDatabaseManager:
    def __init__(self):
        # Use /tmp directory in Lambda for SQLite
        self.db_path = "/tmp/support_portal.db"
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        # Check for PostgreSQL URL first
        database_url = os.environ.get('DATABASE_URL')
        if database_url and 'postgresql' in database_url:
            try:
                import psycopg2
                return psycopg2.connect(database_url)
            except Exception as e:
                print(f"PostgreSQL connection failed, using SQLite: {e}")
        
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tickets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    attachment_url TEXT
                )
            """)
            
            # Ticket files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_files (
                    id TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    file_url TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id)
                )
            """)
            
            # Comments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id)
                )
            """)
            
            conn.commit()

# Repository classes
class TicketRepository:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_ticket(self, subject: str, priority: str, category: str, 
                     description: str, user_id: str, attachment_url: str = None):
        ticket_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tickets (id, subject, priority, category, description, 
                                   status, user_id, created_at, attachment_url)
                VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?)
            """, (ticket_id, subject, priority, category, description, user_id, created_at, attachment_url))
            conn.commit()
            
        return {
            'id': ticket_id,
            'subject': subject,
            'priority': priority,
            'category': category,
            'description': description,
            'status': 'open',
            'user_id': user_id,
            'created_at': created_at,
            'attachment_url': attachment_url
        }
    
    def get_tickets_by_user(self, user_id: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, priority, category, description, status, user_id, created_at, attachment_url
                FROM tickets WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,))
            
            tickets = []
            for row in cursor.fetchall():
                tickets.append({
                    'id': row[0],
                    'subject': row[1],
                    'priority': row[2],
                    'category': row[3],
                    'description': row[4],
                    'status': row[5],
                    'user_id': row[6],
                    'created_at': row[7],
                    'attachment_url': row[8]
                })
            return tickets
    
    def get_ticket(self, ticket_id: str, user_id: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, priority, category, description, status, user_id, created_at, attachment_url
                FROM tickets WHERE id = ? AND user_id = ?
            """, (ticket_id, user_id))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'subject': row[1],
                    'priority': row[2],
                    'category': row[3],
                    'description': row[4],
                    'status': row[5],
                    'user_id': row[6],
                    'created_at': row[7],
                    'attachment_url': row[8]
                }
            return None
    
    def get_metrics_for_user(self, user_id: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total tickets
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ?", (user_id,))
            total = cursor.fetchone()[0]
            
            # Open tickets
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND status = 'open'", (user_id,))
            open_count = cursor.fetchone()[0]
            
            # Resolved tickets
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND status != 'open'", (user_id,))
            resolved = cursor.fetchone()[0]
            
            return {
                'total': total,
                'open': open_count,
                'resolved': resolved
            }

class CommentRepository:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_comments_for_ticket(self, ticket_id: str):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ticket_id, user_id, comment, created_at
                FROM comments WHERE ticket_id = ? ORDER BY created_at ASC
            """, (ticket_id,))
            
            comments = []
            for row in cursor.fetchall():
                comments.append({
                    'id': row[0],
                    'ticket_id': row[1],
                    'user_id': row[2],
                    'comment': row[3],
                    'created_at': row[4]
                })
            return comments
    
    def create_comment(self, ticket_id: str, user_id: str, comment_text: str):
        comment_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO comments (id, ticket_id, user_id, comment, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (comment_id, ticket_id, user_id, comment_text, created_at))
            conn.commit()
            
        return {
            'id': comment_id,
            'ticket_id': ticket_id,
            'user_id': user_id,
            'comment': comment_text,
            'created_at': created_at
        }

# File upload handler
class S3FileManager:
    def __init__(self):
        self.bucket_name = os.environ.get('S3_BUCKET_NAME')
        self.s3_client = None
        if self.bucket_name:
            try:
                import boto3
                self.s3_client = boto3.client('s3')
            except Exception as e:
                print(f"S3 client initialization failed: {e}")
    
    def upload_file(self, file_data: str, file_name: str, file_type: str = None):
        """Upload base64 file data to S3 or return local path"""
        if not self.s3_client or not self.bucket_name:
            # Fallback to local storage (not recommended for Lambda)
            file_path = f"/tmp/{file_name}"
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(file_data))
            return file_path, len(base64.b64decode(file_data))
        
        try:
            # Upload to S3
            file_key = f"uploads/{uuid.uuid4()}_{file_name}"
            file_content = base64.b64decode(file_data)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=file_type or 'application/octet-stream'
            )
            
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{file_key}"
            return file_url, len(file_content)
            
        except Exception as e:
            print(f"S3 upload failed: {e}")
            raise Exception(f"File upload failed: {str(e)}")

# Initialize components
db_manager = LambdaDatabaseManager()
ticket_repo = TicketRepository(db_manager)
comment_repo = CommentRepository(db_manager)
file_manager = S3FileManager()
slack_notifier = SlackNotifier()

def get_user_id(event):
    """Extract user ID from Lambda event"""
    headers = event.get('headers', {})
    return headers.get('X-User-Id', headers.get('x-user-id', 'demo-user'))

def parse_json_body(event):
    """Parse JSON body from Lambda event"""
    body = event.get('body', '{}')
    if isinstance(body, str):
        return json.loads(body)
    return body

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        print(f"Event: {json.dumps(event)}")
        
        # Handle CORS preflight requests
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Remove API Gateway stage from path if present
        if path.startswith('/prod/'):
            path = path[5:]
        if path.startswith('/dev/'):
            path = path[4:]
        
        user_id = get_user_id(event)
        
        # Route requests
        if method == 'GET' and path == '/':
            return create_response(200, {
                'message': 'Support Portal API with P1 Critical Slack Integration',
                'version': '2.0.0',
                'features': ['P1 Critical Slack Alerts', 'Ticket Management', 'Comments System'],
                'endpoints': [
                    'GET /tickets/my - Get user tickets',
                    'POST /tickets - Create ticket (P1 alerts sent to Slack)',
                    'GET /tickets/{id} - Get ticket details',
                    'GET /tickets/{id}/comments - Get comments',
                    'POST /tickets/{id}/comments - Add comment',
                    'GET /dashboard/metrics - Get metrics'
                ]
            })
        
        elif method == 'GET' and path == '/health':
            return create_response(200, {'status': 'healthy', 'slack_integration': 'enabled'})
        
        elif method == 'GET' and path == '/tickets/my':
            tickets = ticket_repo.get_tickets_by_user(user_id)
            return create_response(200, {'tickets': tickets})
        
        elif method == 'POST' and path == '/tickets':
            body = parse_json_body(event)
            
            # Validate required fields
            required_fields = ['subject', 'priority', 'category', 'description']
            for field in required_fields:
                if not body.get(field):
                    return create_error_response(f"Missing required field: {field}")
            
            # Validate priority
            if body['priority'] not in ['low', 'medium', 'high', 'P1']:
                return create_error_response("Invalid priority. Must be: low, medium, high, or P1")
            
            # Handle file attachment
            attachment_url = None
            if body.get('attachment') and body.get('attachment_name'):
                try:
                    attachment_url, file_size = file_manager.upload_file(
                        body['attachment'],
                        body['attachment_name'],
                        body.get('attachment_type')
                    )
                except Exception as e:
                    return create_error_response(f"File upload failed: {str(e)}")
            
            # Create ticket
            ticket = ticket_repo.create_ticket(
                body['subject'],
                body['priority'],
                body['category'],
                body['description'],
                user_id,
                attachment_url
            )
            
            # Send Slack notification for P1 Critical incidents
            if body['priority'] == 'P1':
                print("🚨 P1 Critical ticket detected - sending Slack alert...")
                slack_sent = slack_notifier.send_p1_notification(ticket)
                if slack_sent:
                    print("✅ P1 Critical Slack alert sent successfully")
                else:
                    print("❌ Failed to send P1 Critical Slack alert")
            
            # Optionally send notifications for other priorities (uncomment if needed)
            # else:
            #     slack_notifier.send_general_notification(ticket)
            
            return create_response(200, {
                'ticket': ticket,
                'slack_notification': 'sent' if body['priority'] == 'P1' else 'skipped'
            })
        
        elif method == 'GET' and path.startswith('/tickets/') and not path.endswith('/comments'):
            # Get single ticket
            ticket_id = path.split('/')[-1]
            ticket = ticket_repo.get_ticket(ticket_id, user_id)
            
            if not ticket:
                return create_error_response("Ticket not found", 404)
            
            return create_response(200, {'ticket': ticket})
        
        elif method == 'GET' and path.endswith('/comments'):
            # Get comments for ticket
            ticket_id = path.split('/')[-2]
            comments = comment_repo.get_comments_for_ticket(ticket_id)
            return create_response(200, {'comments': comments})
        
        elif method == 'POST' and path.endswith('/comments'):
            # Add comment to ticket
            ticket_id = path.split('/')[-2]
            body = parse_json_body(event)
            
            if not body.get('comment', '').strip():
                return create_error_response("Comment cannot be empty")
            
            comment = comment_repo.create_comment(ticket_id, user_id, body['comment'].strip())
            return create_response(200, {'comment': comment})
        
        elif method == 'GET' and path == '/dashboard/metrics':
            metrics = ticket_repo.get_metrics_for_user(user_id)
            return create_response(200, {'metrics': metrics})
        
        else:
            return create_error_response(f"Not found: {method} {path}", 404)
    
    except Exception as e:
        print(f"Lambda error: {str(e)}")
        return create_error_response(f"Internal server error: {str(e)}", 500)

# Test function for local testing
if __name__ == "__main__":
    # Test P1 Critical ticket creation
    test_event = {
        'httpMethod': 'POST',
        'path': '/tickets',
        'headers': {'X-User-Id': 'test-user'},
        'body': json.dumps({
            'subject': 'Database Connection Failed - All Services Down',
            'priority': 'P1',
            'category': 'P1 Critical Incident',
            'description': 'Critical production database outage. All customer-facing services are unavailable. Started at 14:30 UTC. Error: Connection timeout to primary database cluster.'
        })
    }
    
    result = lambda_handler(test_event, {})
    print("Test Result:")
    print(json.dumps(result, indent=2))