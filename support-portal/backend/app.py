#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Support Portal API - Standalone Backend
AWS Lambda-ready Python script with FastAPI

Features:
- Create tickets with file attachments
- S3 upload with local fallback  
- SQLite database with RDS fallback
- All endpoints needed by the Next.js frontend
- Environment-based configuration
- Ready for AWS Lambda deployment

Run locally: python app.py
API will be available at: http://localhost:8000
"""

import os
import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import uuid
import base64
import sqlite3
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

# FastAPI imports with error handling
try:
    from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"❌ Missing FastAPI dependencies: {e}")
    print("Install with: pip install fastapi uvicorn python-multipart")
    sys.exit(1)

# AWS and other optional imports
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

# HTTP requests for Slack integration
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    print("⚠️ requests not available - Slack notifications disabled")
    HAS_REQUESTS = False

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Import shared components
from shared import (
    Config, DatabaseManager, StorageManager, TicketRepository,
    create_error_response, ApiResponse, Ticket
)

# Import authentication components
from auth_models import AuthManager

# Import enhanced Slack channel manager
try:
    from slack_channel_manager import SlackChannelManager
    HAS_SLACK_MANAGER = True
except ImportError:
    HAS_SLACK_MANAGER = False
    print("⚠️ slack_channel_manager not available")

# Import email notifier
try:
    from email_notifier import EmailNotifier
    HAS_EMAIL_NOTIFIER = True
except ImportError:
    HAS_EMAIL_NOTIFIER = False
    print("⚠️ email_notifier not available")

# Import DynamoDB manager
try:
    from dynamodb_manager import DynamoDBManager
    HAS_DYNAMODB = True
except ImportError:
    HAS_DYNAMODB = False
    print("⚠️ dynamodb_manager not available - using SQLite for P1 incidents")

# Slack Integration
class SlackNotifier:
    """Handles Slack notifications for P1 Critical incidents"""
    
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
        self.enabled = HAS_REQUESTS
    
    def send_p1_notification(self, ticket: Dict[str, Any]) -> bool:
        """Send P1 Critical incident notification to Slack"""
        if not self.enabled:
            print("⚠️ Slack notifications disabled - requests library not available")
            return False
            
        try:
            message = self._create_p1_message(ticket)
            
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ P1 Slack notification sent for ticket {ticket.get('id', 'unknown')[:8]}")
                return True
            else:
                print(f"❌ Slack notification failed: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            print(f"❌ Slack notification error: {str(e)}")
            return False
    
    def _create_p1_message(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Create rich Slack message for P1 incident"""
        ticket_id = ticket.get('id', 'UNKNOWN')[:8]
        incident_id = ticket.get('incident_id', f'P1-{ticket_id}')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Extract merchant and user information
        merchant_name = ticket.get('merchant_name', 'Unknown Merchant')
        user_name = ticket.get('user_name', 'Unknown User')
        user_email = ticket.get('user_email', '')
        
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 P1 CRITICAL INCIDENT ALERT"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Incident ID:* {incident_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Priority:* {ticket.get('priority', 'P1')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Merchant:* {merchant_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*User:* {user_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Email:* {user_email}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Created:* {created_at}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Subject:* {ticket.get('subject', 'P1 Critical Incident')}\n\n*Description:* {ticket.get('description', 'No description provided')[:500]}{'...' if len(ticket.get('description', '')) > 500 else ''}"
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
                            "text": f"🔥 *IMMEDIATE ACTION REQUIRED* - P1 Critical incidents require immediate response | Ticket ID: `{ticket_id}`"
                        }
                    ]
                }
            ]
        }

# Ensure upload folder exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Data Models (additional ones not in shared)
@dataclass
class TicketFile:
    id: str
    ticket_id: str
    file_url: str
    file_name: str
    created_at: str

@dataclass
class Comment:
    id: str
    ticket_id: str
    user_id: str
    comment: str
    created_at: str

# Pydantic models for API
class CreateTicketRequest(BaseModel):
    subject: str
    priority: str
    category: str
    description: str
    attachment: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None

class CreateCommentRequest(BaseModel):
    comment: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateMerchantRequest(BaseModel):
    merchant_name: str
    company_name: str
    email: str
    phone: Optional[str] = None

class CreateUserRequest(BaseModel):
    merchant_id: str
    username: str
    email: str
    password: str
    full_name: str
    role: Optional[str] = "user"

# Extended Repository Classes
class ExtendedTicketRepository(TicketRepository):
    def __init__(self):
        self.s3_client = None
        if HAS_BOTO3 and Config.AWS_ACCESS_KEY_ID and Config.S3_BUCKET_NAME:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                    region_name=Config.AWS_REGION
                )
                print("✅ S3 client initialized")
            except Exception as e:
                print(f"⚠️ S3 initialization failed: {e}")
    
    def upload_file(self, file_data: str, file_name: str, file_type: str = None):
        """Upload file to S3 or local storage"""
        try:
            # Decode base64 file data
            if ',' in file_data:
                file_data = file_data.split(',', 1)[1]
            
            file_bytes = base64.b64decode(file_data)
            file_size = len(file_bytes)
            
            # Check file size
            if file_size > Config.MAX_FILE_SIZE:
                raise ValueError(f"File size ({file_size}) exceeds limit ({Config.MAX_FILE_SIZE})")
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{file_name}"
            
            # Try S3 upload first
            if self.s3_client and Config.S3_BUCKET_NAME:
                try:
                    self.s3_client.put_object(
                        Bucket=Config.S3_BUCKET_NAME,
                        Key=unique_filename,
                        Body=file_bytes,
                        ContentType=file_type or 'application/octet-stream'
                    )
                    file_url = f"https://{Config.S3_BUCKET_NAME}.s3.{Config.AWS_REGION}.amazonaws.com/{unique_filename}"
                    print(f"✅ File uploaded to S3: {file_url}")
                    return file_url, file_size
                except Exception as e:
                    print(f"⚠️ S3 upload failed, falling back to local storage: {e}")
            
            # Fallback to local storage
            local_path = Path(Config.UPLOAD_FOLDER) / unique_filename
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            
            file_url = f"/uploads/{unique_filename}"
            print(f"✅ File saved locally: {file_url}")
            return file_url, file_size
            
        except Exception as e:
            print(f"❌ File upload failed: {e}")
            raise HTTPException(status_code=400, detail=f"File upload failed: {str(e)}")

# Repository Classes
class TicketRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_ticket(self, subject: str, priority: str, category: str, 
                     description: str, user_id: str, attachment_url: str = None,
                     merchant_id: str = None, merchant_name: str = None,
                     user_name: str = None, user_email: str = None) -> Ticket:
        """Create a new ticket"""
        ticket_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tickets (id, subject, priority, category, description, 
                                   status, user_id, created_at, attachment_url,
                                   merchant_id, merchant_name, user_name, user_email)
                VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?)
            """, (ticket_id, subject, priority, category, description, user_id, created_at, attachment_url,
                  merchant_id, merchant_name, user_name, user_email))
            conn.commit()
        
        return Ticket(
            id=ticket_id,
            subject=subject,
            priority=priority,
            category=category,
            description=description,
            status='open',
            user_id=user_id,
            created_at=created_at,
            attachment_url=attachment_url
        )
    
    def get_my_tickets(self, user_id: str) -> List[Dict]:
        """Get all tickets for a user with P1 incident info"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.subject, t.priority, t.category, t.description, t.status, 
                       t.user_id, t.created_at, t.attachment_url,
                       p.incident_id, p.status as p1_status
                FROM tickets t
                LEFT JOIN p1_incidents p ON t.id = p.ticket_id
                WHERE t.user_id = ? 
                ORDER BY t.created_at DESC
            """, (user_id,))
            
            tickets = []
            for row in cursor.fetchall():
                ticket = {
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
                # Add P1 incident info if exists
                if row[9]:  # incident_id
                    ticket['p1_incident'] = {
                        'incident_id': row[9],
                        'status': row[10]
                    }
                tickets.append(ticket)
            return tickets
    
    def get_ticket(self, ticket_id: str, user_id: str = None) -> Optional[Dict]:
        """Get a specific ticket"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id, subject, priority, category, description, status, 
                       user_id, created_at, attachment_url
                FROM tickets WHERE id = ?
            """
            params = [ticket_id]
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            cursor.execute(query, params)
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
    
    def get_dashboard_metrics(self, user_id: str = None) -> Dict[str, int]:
        """Get dashboard metrics"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            base_query = "SELECT COUNT(*) FROM tickets"
            where_clause = " WHERE user_id = ?" if user_id else ""
            params = [user_id] if user_id else []
            
            # Total tickets
            cursor.execute(base_query + where_clause, params)
            total = cursor.fetchone()[0]
            
            # Open tickets  
            cursor.execute(base_query + where_clause + (" AND" if user_id else " WHERE") + " status IN ('open', 'in_progress')", params)
            open_tickets = cursor.fetchone()[0]
            
            # Resolved tickets
            cursor.execute(base_query + where_clause + (" AND" if user_id else " WHERE") + " status IN ('resolved', 'closed')", params)
            resolved = cursor.fetchone()[0]
            
            return {
                'total': total,
                'open': open_tickets, 
                'resolved': resolved
            }

class CommentRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_comments_for_ticket(self, ticket_id: str) -> List[Dict]:
        """Get all comments for a ticket"""
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
        """Create a new comment for a ticket"""
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
    
    def create_demo_comment(self, ticket_id: str, user_id: str):
        """Create a demo comment for development"""
        comment_text = "Thank you for submitting your ticket. We've received your request and will respond within 24 hours."
        return self.create_comment(ticket_id, 'support-team', comment_text)

class TicketFileRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_ticket_file(self, ticket_id: str, file_url: str, file_name: str):
        """Save ticket file record"""
        file_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ticket_files (id, ticket_id, file_url, file_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, ticket_id, file_url, file_name, created_at))
            conn.commit()

class P1IncidentRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_p1_incident(self, ticket_id: str, slack_notification_sent: bool = False, 
                          slack_message_id: str = None, slack_channel_id: str = None) -> Dict:
        """Create a P1 incident record with Slack tracking"""
        incident_id = f"P1-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        p1_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        
        slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO p1_incidents (
                    id, ticket_id, incident_id, slack_channel_id, slack_message_id,
                    slack_notification_sent, slack_notification_sent_at, slack_webhook_url,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
            """, (
                p1_id, ticket_id, incident_id, slack_channel_id, slack_message_id,
                slack_notification_sent, 
                datetime.now(timezone.utc).isoformat() if slack_notification_sent else None,
                slack_webhook_url, created_at
            ))
            conn.commit()
        
        return {
            'id': p1_id,
            'ticket_id': ticket_id,
            'incident_id': incident_id,
            'slack_notification_sent': slack_notification_sent,
            'slack_message_id': slack_message_id,
            'slack_channel_id': slack_channel_id,
            'slack_webhook_url': slack_webhook_url,
            'status': 'active',
            'created_at': created_at
        }
    
    def get_p1_incidents(self, user_id: str = None) -> List[Dict]:
        """Get all P1 incidents, optionally filtered by user"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    SELECT p.id, p.ticket_id, p.incident_id, p.slack_channel_id, p.slack_message_id,
                           p.slack_notification_sent, p.slack_notification_sent_at, p.slack_webhook_url,
                           p.status, p.created_at, p.resolved_at,
                           t.subject, t.priority, t.category, t.description
                    FROM p1_incidents p
                    JOIN tickets t ON p.ticket_id = t.id
                    WHERE t.user_id = ?
                    ORDER BY p.created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT p.id, p.ticket_id, p.incident_id, p.slack_channel_id, p.slack_message_id,
                           p.slack_notification_sent, p.slack_notification_sent_at, p.slack_webhook_url,
                           p.status, p.created_at, p.resolved_at,
                           t.subject, t.priority, t.category, t.description
                    FROM p1_incidents p
                    JOIN tickets t ON p.ticket_id = t.id
                    ORDER BY p.created_at DESC
                """)
            
            incidents = []
            for row in cursor.fetchall():
                incidents.append({
                    'id': row[0],
                    'ticket_id': row[1],
                    'incident_id': row[2],
                    'slack_channel_id': row[3],
                    'slack_message_id': row[4],
                    'slack_notification_sent': bool(row[5]),
                    'slack_notification_sent_at': row[6],
                    'slack_webhook_url': row[7],
                    'status': row[8],
                    'created_at': row[9],
                    'resolved_at': row[10],
                    'ticket': {
                        'subject': row[11],
                        'priority': row[12],
                        'category': row[13],
                        'description': row[14]
                    }
                })
            return incidents
    
    def get_p1_incident_by_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Get P1 incident by ticket ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ticket_id, incident_id, slack_channel_id, slack_message_id,
                       slack_notification_sent, slack_notification_sent_at, slack_webhook_url,
                       status, created_at, resolved_at
                FROM p1_incidents WHERE ticket_id = ?
            """, (ticket_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'ticket_id': row[1],
                    'incident_id': row[2],
                    'slack_channel_id': row[3],
                    'slack_message_id': row[4],
                    'slack_notification_sent': bool(row[5]),
                    'slack_notification_sent_at': row[6],
                    'slack_webhook_url': row[7],
                    'status': row[8],
                    'created_at': row[9],
                    'resolved_at': row[10]
                }
            return None
    
    def get_p1_incident_by_incident_id(self, incident_id: str) -> Optional[Dict]:
        """Get P1 incident by incident ID with ticket details"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.ticket_id, p.incident_id, p.slack_channel_id, p.slack_message_id,
                       p.slack_notification_sent, p.slack_notification_sent_at, p.slack_webhook_url,
                       p.status, p.created_at, p.resolved_at,
                       t.subject, t.description, t.priority, t.category, t.user_id
                FROM p1_incidents p
                JOIN tickets t ON p.ticket_id = t.id
                WHERE p.incident_id = ?
            """, (incident_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'ticket_id': row[1],
                    'incident_id': row[2],
                    'slack_channel_id': row[3],
                    'slack_message_id': row[4],
                    'slack_notification_sent': bool(row[5]),
                    'slack_notification_sent_at': row[6],
                    'slack_webhook_url': row[7],
                    'status': row[8],
                    'created_at': row[9],
                    'resolved_at': row[10],
                    'ticket': {
                        'subject': row[11],
                        'description': row[12],
                        'priority': row[13],
                        'category': row[14],
                        'user_id': row[15]
                    }
                }
            return None
    
    def update_slack_notification(self, ticket_id: str, slack_message_id: str = None, 
                                 slack_channel_id: str = None, notification_sent: bool = True):
        """Update Slack notification details for P1 incident"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE p1_incidents 
                SET slack_notification_sent = ?, 
                    slack_notification_sent_at = ?,
                    slack_message_id = COALESCE(?, slack_message_id),
                    slack_channel_id = COALESCE(?, slack_channel_id)
                WHERE ticket_id = ?
            """, (
                notification_sent,
                datetime.now(timezone.utc).isoformat() if notification_sent else None,
                slack_message_id,
                slack_channel_id,
                ticket_id
            ))
            conn.commit()
    
    def resolve_p1_incident(self, ticket_id: str):
        """Mark P1 incident as resolved"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE p1_incidents 
                SET status = 'resolved', resolved_at = ?
                WHERE ticket_id = ?
            """, (datetime.now(timezone.utc).isoformat(), ticket_id))
            conn.commit()

# Initialize components
db_manager = DatabaseManager()
storage_manager = StorageManager()
auth_manager = AuthManager(db_manager)
ticket_repo = TicketRepository(db_manager)
comment_repo = CommentRepository(db_manager)
file_repo = TicketFileRepository(db_manager)
p1_incident_repo = P1IncidentRepository(db_manager)
slack_notifier = SlackNotifier()

# Initialize Email Notifier
email_notifier = None
if HAS_EMAIL_NOTIFIER:
    email_notifier = EmailNotifier()
    if email_notifier.enabled:
        print("✅ Email Notifier initialized")
    else:
        print("⚠️ Email Notifier disabled - set SMTP credentials in .env")
else:
    print("⚠️ Email Notifier not available")

# Initialize Slack Channel Manager for threaded conversations with multi-client support
# TODO: Replace these with your actual Slack Bot Token and Channel ID
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")  # xoxb-...
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")  # Default channel (optional with multi-client setup)

slack_channel_manager = None
if HAS_SLACK_MANAGER and SLACK_BOT_TOKEN:
    # Pass database connection to support merchant-specific channel routing
    db_conn = db_manager.get_connection()
    slack_channel_manager = SlackChannelManager(SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, db_conn)
    print("✅ Slack Channel Manager initialized with multi-client support")
else:
    print("⚠️ Slack Channel Manager not available - set SLACK_BOT_TOKEN")

# Initialize DynamoDB Manager for P1 Incidents (Production)
dynamodb_manager = None
use_dynamodb = os.getenv("USE_DYNAMODB", "false").lower() == "true"
if HAS_DYNAMODB and use_dynamodb:
    try:
        dynamodb_manager = DynamoDBManager()
        print("✅ DynamoDB Manager initialized - P1 incidents will be stored in DynamoDB")
    except Exception as e:
        print(f"⚠️ DynamoDB initialization failed, falling back to SQLite: {e}")
else:
    print("ℹ️ Using SQLite for P1 incidents (set USE_DYNAMODB=true for production)")

# FastAPI app
app = FastAPI(
    title="Support Portal API",
    description="Standalone Support Portal Backend - AWS Lambda Ready",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def get_user_id(request: Request) -> str:
    """Extract user ID from request headers"""
    user_id = request.headers.get("X-User-Id") or Config.DEFAULT_USER_ID
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return user_id

def get_user_from_token(request: Request) -> Optional[Dict]:
    """Get user info from session token"""
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]  # Remove "Bearer " prefix
        return auth_manager.verify_session(token)
    return None

def get_user_info_or_default(request: Request) -> Dict:
    """Get authenticated user info or use default"""
    user_info = get_user_from_token(request)
    
    if user_info:
        return user_info
    
    # Fallback to X-User-Id header (for backwards compatibility)
    user_id = request.headers.get("X-User-Id") or Config.DEFAULT_USER_ID
    return {
        'user_id': user_id,
        'username': user_id,
        'full_name': 'Demo User',
        'merchant_id': 'demo',
        'merchant_name': 'Demo Company',
        'email': 'demo@example.com'
    }

def create_response(data: Any, message: str = "Success") -> Dict:
    """Create standardized API response"""
    return {"success": True, "message": message, "data": data}

def create_error_response(message: str, status_code: int = 400) -> HTTPException:
    """Create error response"""
    return HTTPException(status_code=status_code, detail=message)

# API Routes

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Support Portal API", 
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# ============================================
# Authentication Endpoints
# ============================================

@app.post("/auth/login")
async def login(login_data: LoginRequest):
    """Login user and return session token"""
    try:
        user_info = auth_manager.authenticate_user(login_data.username, login_data.password)
        
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create session
        token = auth_manager.create_session(user_info['user_id'], user_info['merchant_id'])
        
        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "token": token,
                "user": user_info
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/auth/logout")
async def logout(request: Request):
    """Logout user (invalidate session)"""
    # In a full implementation, we would delete the session from database
    return {"success": True, "message": "Logged out successfully"}

@app.get("/auth/me")
async def get_current_user(request: Request):
    """Get current authenticated user info"""
    user_info = get_user_from_token(request)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {"success": True, "data": user_info}

@app.post("/auth/merchants")
async def create_merchant(merchant_data: CreateMerchantRequest):
    """Create a new merchant (admin only)"""
    try:
        merchant = auth_manager.create_merchant(
            merchant_name=merchant_data.merchant_name,
            company_name=merchant_data.company_name,
            email=merchant_data.email,
            phone=merchant_data.phone
        )
        
        return {
            "success": True,
            "message": "Merchant created successfully",
            "data": {
                "merchant_id": merchant.merchant_id,
                "merchant_name": merchant.merchant_name,
                "api_key": merchant.api_key
            }
        }
    except Exception as e:
        print(f"❌ Create merchant error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/users")
async def create_user(user_data: CreateUserRequest):
    """Create a new user under a merchant"""
    try:
        user = auth_manager.create_user(
            merchant_id=user_data.merchant_id,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        return {
            "success": True,
            "message": "User created successfully",
            "data": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
        }
    except Exception as e:
        print(f"❌ Create user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/merchants/{merchant_id}")
async def get_merchant(merchant_id: str):
    """Get merchant details"""
    merchant = auth_manager.get_merchant(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return {"success": True, "data": merchant}

@app.get("/auth/merchants/{merchant_id}/users")
async def get_merchant_users(merchant_id: str):
    """Get all users for a merchant"""
    users = auth_manager.get_users_by_merchant(merchant_id)
    return {"success": True, "data": users}

# ============================================
# Ticket Endpoints
# ============================================

@app.post("/tickets")
async def create_ticket(request: Request, ticket_data: CreateTicketRequest):
    """Create a new ticket with optional file attachment"""
    try:
        # Get authenticated user info
        user_info = get_user_info_or_default(request)
        
        # Validate required fields
        if not all([ticket_data.subject, ticket_data.priority, ticket_data.category, ticket_data.description]):
            raise create_error_response("Missing required fields")
        
        # Validate priority
        if ticket_data.priority not in ["low", "medium", "high", "P1"]:
            raise create_error_response("Invalid priority. Must be: low, medium, high, or P1")
        
        attachment_url = None
        
        # Handle file attachment if provided
        if ticket_data.attachment and ticket_data.attachment_name:
            try:
                attachment_url, file_size = storage_manager.upload_file(
                    ticket_data.attachment,
                    ticket_data.attachment_name,
                    ticket_data.attachment_type
                )
                print(f"✅ File uploaded: {attachment_url} ({file_size} bytes)")
            except Exception as e:
                print(f"❌ File upload failed: {e}")
                raise create_error_response(f"File upload failed: {str(e)}")
        
        # Create ticket with merchant and user information
        ticket = ticket_repo.create_ticket(
            subject=ticket_data.subject,
            priority=ticket_data.priority,
            category=ticket_data.category,
            description=ticket_data.description,
            user_id=user_info['user_id'],
            attachment_url=attachment_url,
            merchant_id=user_info.get('merchant_id'),
            merchant_name=user_info.get('merchant_name'),
            user_name=user_info.get('full_name'),
            user_email=user_info.get('email')
        )
        
        # Save file record if attachment exists
        if attachment_url:
            file_repo.save_ticket_file(
                ticket_id=ticket.id,
                file_url=attachment_url,
                file_name=ticket_data.attachment_name
            )
        
        # Create demo comment for development
        comment_repo.create_demo_comment(ticket.id, user_info['user_id'])
        
        # Handle P1 Critical tickets with incident tracking
        p1_incident = None
        slack_sent = False
        email_sent = False
        thread_ts = None
        
        if ticket_data.priority == 'P1':
            # Create P1 incident record first
            p1_incident = p1_incident_repo.create_p1_incident(ticket.id)
            print(f"🚨 P1 Incident created: {p1_incident['incident_id']}")
            
            # Prepare incident data for notifications with merchant info
            ticket_dict = asdict(ticket)
            ticket_dict['incident_id'] = p1_incident['incident_id']
            ticket_dict['merchant_id'] = user_info.get('merchant_id', None)  # For channel routing
            ticket_dict['merchant_name'] = user_info.get('merchant_name', 'Unknown')
            ticket_dict['user_name'] = user_info.get('full_name', 'Unknown')
            ticket_dict['user_email'] = user_info.get('email', '')
            ticket_dict['category'] = ticket_data.category
            ticket_dict['ticket_id'] = ticket.id
            ticket_dict['created_at'] = ticket.created_at
            
            # Send Email Notification to User
            if email_notifier and email_notifier.enabled:
                try:
                    email_sent = email_notifier.send_p1_notification(ticket_dict)
                    if email_sent:
                        print(f"📧 P1 email notification sent to {ticket_dict['user_email']}")
                    else:
                        print(f"⚠️ P1 email notification failed")
                except Exception as e:
                    print(f"❌ Email notification error: {e}")
            
            # Try new Slack Channel Manager first (threaded conversations with multi-client routing)
            if slack_channel_manager:
                try:
                    thread_ts = slack_channel_manager.post_incident(ticket_dict)
                    if thread_ts:
                        slack_sent = True
                        # Update incident with thread_ts
                        with db_manager.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE p1_incidents 
                                SET slack_thread_ts = ?, slack_notification_sent = 1,
                                    slack_notification_sent_at = ?
                                WHERE ticket_id = ?
                            """, (thread_ts, datetime.now(timezone.utc).isoformat(), ticket.id))
                            conn.commit()
                        print(f"✅ P1 posted to Slack channel (thread: {thread_ts})")
                except Exception as e:
                    print(f"⚠️ Slack Channel Manager failed: {e}")
            
            # Fallback to webhook notification
            if not slack_sent:
                try:
                    slack_sent = slack_notifier.send_p1_notification(ticket_dict)
                    p1_incident_repo.update_slack_notification(
                        ticket_id=ticket.id,
                        notification_sent=slack_sent
                    )
                    
                    if slack_sent:
                        print(f"📱 P1 Slack webhook sent for incident {p1_incident['incident_id']}")
                    else:
                        print(f"❌ P1 Slack alert failed for incident {p1_incident['incident_id']}")
                        
                except Exception as e:
                    print(f"⚠️ P1 Slack notification failed: {e}")
                    p1_incident_repo.update_slack_notification(
                        ticket_id=ticket.id,
                        notification_sent=False
                    )
        
        print(f"✅ Ticket created: {ticket.id}")
        response_data = {"ticket": asdict(ticket)}
        
        # Add P1 incident details to response
        if p1_incident:
            response_data["p1_incident"] = p1_incident
            response_data["slack_notification"] = "sent" if slack_sent else "failed"
            response_data["email_notification"] = "sent" if email_sent else "failed"
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create ticket error: {e}")
        raise create_error_response(f"Failed to create ticket: {str(e)}", 500)

@app.get("/tickets/my")
async def get_my_tickets(request: Request):
    """Get all tickets for the current user"""
    try:
        user_id = get_user_id(request)
        tickets = ticket_repo.get_my_tickets(user_id)
        print(f"✅ Fetched {len(tickets)} tickets for user {user_id}")
        return {"tickets": tickets}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get my tickets error: {e}")
        raise create_error_response(f"Failed to fetch tickets: {str(e)}", 500)

@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, request: Request):
    """Get a specific ticket"""
    try:
        user_id = get_user_id(request)
        ticket = ticket_repo.get_ticket(ticket_id, user_id)
        
        if not ticket:
            raise create_error_response("Ticket not found", 404)
        
        print(f"✅ Fetched ticket: {ticket_id}")
        return {"ticket": ticket}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get ticket error: {e}")
        raise create_error_response(f"Failed to fetch ticket: {str(e)}", 500)

@app.get("/tickets/{ticket_id}/comments")
async def get_ticket_comments(ticket_id: str):
    """Get all comments for a ticket"""
    try:
        comments = comment_repo.get_comments_for_ticket(ticket_id)
        print(f"✅ Fetched {len(comments)} comments for ticket {ticket_id}")
        return {"comments": comments}
        
    except Exception as e:
        print(f"❌ Get comments error: {e}")
        raise create_error_response(f"Failed to fetch comments: {str(e)}", 500)

@app.post("/tickets/{ticket_id}/comments")
async def create_ticket_comment(request: Request, ticket_id: str, comment_data: CreateCommentRequest):
    """Create a new comment for a ticket"""
    try:
        user_id = get_user_id(request)
        
        # Validate comment text
        if not comment_data.comment.strip():
            raise create_error_response("Comment cannot be empty")
        
        # Create comment
        comment = comment_repo.create_comment(ticket_id, user_id, comment_data.comment.strip())
        print(f"✅ Comment created for ticket {ticket_id} by {user_id}")
        return {"comment": comment}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create comment error: {e}")
        raise create_error_response(f"Failed to create comment: {str(e)}", 500)

@app.get("/dashboard/metrics")
async def get_dashboard_metrics(request: Request):
    """Get dashboard metrics for the current user"""
    try:
        user_id = get_user_id(request)
        metrics = ticket_repo.get_dashboard_metrics(user_id)
        print(f"✅ Dashboard metrics for {user_id}: {metrics}")
        return {"metrics": metrics}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get metrics error: {e}")
        raise create_error_response(f"Failed to fetch metrics: {str(e)}", 500)

@app.get("/p1-incidents")
async def get_p1_incidents(request: Request):
    """Get all P1 Critical incidents for the current user"""
    try:
        user_id = get_user_id(request)
        incidents = p1_incident_repo.get_p1_incidents(user_id)
        print(f"✅ Fetched {len(incidents)} P1 incidents for user {user_id}")
        return {"p1_incidents": incidents}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get P1 incidents error: {e}")
        raise create_error_response(f"Failed to fetch P1 incidents: {str(e)}", 500)

@app.get("/p1-incidents/by-ticket/{ticket_id}")
async def get_p1_incident_by_ticket(ticket_id: str, request: Request):
    """Get P1 incident details for a specific ticket"""
    try:
        user_id = get_user_id(request)
        
        # First check if user owns the ticket
        ticket = ticket_repo.get_ticket(ticket_id, user_id)
        if not ticket:
            raise create_error_response("Ticket not found", 404)
        
        incident = p1_incident_repo.get_p1_incident_by_ticket(ticket_id)
        if not incident:
            raise create_error_response("P1 incident not found for this ticket", 404)
        
        print(f"✅ Fetched P1 incident for ticket {ticket_id}")
        return {"p1_incident": incident}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get P1 incident error: {e}")
        raise create_error_response(f"Failed to fetch P1 incident: {str(e)}", 500)

@app.get("/p1-incidents/by-incident/{incident_id}")
async def get_p1_incident_by_id(incident_id: str, request: Request):
    """Get P1 incident details by incident ID"""
    try:
        user_id = get_user_id(request)
        
        incident = p1_incident_repo.get_p1_incident_by_incident_id(incident_id)
        if not incident:
            raise create_error_response("P1 incident not found", 404)
        
        # Allow viewing all incidents (removed ownership check for demo purposes)
        # if incident['ticket']['user_id'] != user_id:
        #     raise create_error_response("Access denied", 403)
        
        print(f"✅ Fetched P1 incident: {incident_id}")
        return {"p1_incident": incident}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get P1 incident error: {e}")
        raise create_error_response(f"Failed to fetch P1 incident: {str(e)}", 500)

@app.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, request: Request):
    """Update ticket status (resolve, close, reopen, etc.)"""
    try:
        user_id = get_user_id(request)
        
        # Parse request body
        body = await request.json()
        new_status = body.get('status')
        resolution_note = body.get('resolution_note', '')
        
        if not new_status:
            raise create_error_response("Status is required")
        
        if new_status not in ['open', 'in_progress', 'resolved', 'closed']:
            raise create_error_response("Invalid status. Must be: open, in_progress, resolved, or closed")
        
        # Check if user owns the ticket
        ticket = ticket_repo.get_ticket(ticket_id, user_id)
        if not ticket:
            raise create_error_response("Ticket not found", 404)
        
        # Update ticket status in database
        with ticket_repo.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tickets 
                SET status = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (new_status, datetime.now(timezone.utc).isoformat(), ticket_id, user_id))
            
            if cursor.rowcount == 0:
                raise create_error_response("Failed to update ticket status", 500)
            
            conn.commit()
        
        # If this is a P1 incident being resolved, update the P1 incident status
        if new_status in ['resolved', 'closed']:
            p1_incident = p1_incident_repo.get_p1_incident_by_ticket(ticket_id)
            if p1_incident:
                p1_incident_repo.resolve_p1_incident(ticket_id)
                print(f"🚨 P1 Incident {p1_incident['incident_id']} marked as resolved")
        
        # Add a system comment about the status change
        if resolution_note:
            comment_text = f"Status updated to '{new_status}': {resolution_note}"
        else:
            comment_text = f"Status updated to '{new_status}'"
            
        comment_repo.create_comment(ticket_id, 'system', comment_text)
        
        print(f"✅ Ticket {ticket_id} status updated to '{new_status}' by {user_id}")
        
        return {
            "success": True,
            "message": f"Ticket status updated to '{new_status}'",
            "ticket_id": ticket_id,
            "status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update ticket status error: {e}")
        raise create_error_response(f"Failed to update ticket status: {str(e)}", 500)

# P1 Critical tickets are now handled through regular tickets with priority='P1'

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"❌ Unhandled error: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "success": False, 
            "message": "Internal server error",
            "detail": str(exc) if Config.DEBUG else "Something went wrong"
        }
    )

# ============================================
# Slack Communication Endpoints
# ============================================

@app.post("/api/incidents/{incident_id}/send-message")
async def send_message_to_slack(incident_id: str, request: Request):
    """Send user message to Slack channel"""
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        user_name = body.get("user_name", "User")
        
        if not message:
            raise create_error_response("Message cannot be empty", 400)
        
        # Get P1 incident details including thread_ts
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ticket_id, slack_webhook_url, slack_channel_id, slack_thread_ts
                FROM p1_incidents
                WHERE incident_id = ? AND status = 'active'
            """, (incident_id,))
            
            row = cursor.fetchone()
            if not row:
                raise create_error_response("Active incident not found", 404)
            
            ticket_id, webhook_url, channel_id, thread_ts = row
        
        # Send message to Slack using Channel Manager (threaded) or fallback to webhook
        slack_success = False
        
        if slack_channel_manager and thread_ts:
            # Use threaded reply for WhatsApp-like experience
            try:
                slack_success = slack_channel_manager.post_reply(
                    thread_ts=thread_ts,
                    message=message,
                    user_name=user_name
                )
                if slack_success:
                    print(f"✅ User message posted as thread reply for incident {incident_id}")
            except Exception as e:
                print(f"⚠️ Slack Channel Manager failed: {e}")
        
        # Fallback to webhook if no thread_ts or channel manager failed
        if not slack_success and HAS_REQUESTS and webhook_url:
            slack_message = {
                "text": f"💬 *Message from {user_name}:*\n{message}",
                "username": user_name,
                "icon_emoji": ":speech_balloon:"
            }
            
            response = requests.post(
                webhook_url,
                json=slack_message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to send message to Slack: {response.status_code}")
                raise create_error_response("Failed to send message to Slack", 500)
            
            slack_success = True
            print(f"✅ User message sent to Slack webhook for incident {incident_id}")
        
        # Store message in database for history
        message_id = f"msg-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create slack_messages table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS slack_messages (
                    message_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    ticket_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    message_text TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                INSERT INTO slack_messages 
                (message_id, incident_id, ticket_id, user_name, message_text, direction, created_at)
                VALUES (?, ?, ?, ?, ?, 'outbound', ?)
            """, (
                message_id,
                incident_id,
                ticket_id,
                user_name,
                message,
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
        
        return {
            "status": "success",
            "message_id": message_id,
            "sent_to_slack": HAS_REQUESTS and webhook_url is not None
        }
        
    except Exception as e:
        print(f"❌ Send message error: {e}")
        raise create_error_response(f"Failed to send message: {str(e)}", 500)

@app.get("/api/incidents/{incident_id}/messages")
async def get_incident_messages(incident_id: str):
    """Get all messages for an incident"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS slack_messages (
                    message_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    ticket_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    message_text TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                SELECT message_id, user_name, message_text, direction, created_at
                FROM slack_messages
                WHERE incident_id = ?
                ORDER BY created_at ASC
            """, (incident_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "user": row[1],
                    "message": row[2],
                    "type": "operations" if row[3] == "inbound" else "outbound",
                    "timestamp": row[4]
                })
        
        return {"messages": messages}
        
    except Exception as e:
        print(f"❌ Get messages error: {e}")
        raise create_error_response(f"Failed to fetch messages: {str(e)}", 500)

@app.post("/api/incidents/{incident_id}/sync-slack-messages")
async def sync_slack_messages(incident_id: str):
    """
    SYNC ENDPOINT: Fetch messages from Slack and sync to database
    This allows WhatsApp-like experience WITHOUT ngrok!
    Frontend calls this to pull messages from Slack
    """
    try:
        if not slack_channel_manager:
            raise create_error_response("Slack Channel Manager not configured", 503)
        
        # Get incident details including thread_ts
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ticket_id, slack_thread_ts
                FROM p1_incidents
                WHERE incident_id = ?
            """, (incident_id,))
            
            row = cursor.fetchone()
            if not row:
                raise create_error_response("Incident not found", 404)
            
            ticket_id, thread_ts = row
            
            if not thread_ts:
                return {"synced": 0, "message": "No Slack thread for this incident"}
        
        # Fetch thread replies from Slack
        print(f"🔄 Syncing Slack messages for incident {incident_id} (thread: {thread_ts})")
        slack_messages = slack_channel_manager.get_thread_replies(thread_ts)
        
        if not slack_messages:
            return {"synced": 0, "message": "No new messages in Slack"}
        
        # Get existing message IDs to avoid duplicates
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_id FROM slack_messages WHERE incident_id = ?
            """, (incident_id,))
            existing_ids = set(row[0] for row in cursor.fetchall())
        
        # Store new messages from Slack
        synced_count = 0
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            for msg in slack_messages:
                # Use Slack's timestamp as message ID
                message_id = f"slack-{msg.get('ts', '')}"
                
                # Skip if already in database
                if message_id in existing_ids:
                    continue
                
                message_text = msg.get('text', '')
                user_id = msg.get('user', 'unknown')
                timestamp = msg.get('ts', '')
                
                # Clean up Slack formatting for display
                # Remove <!here>, <!channel>, emojis like :speech_balloon:, and bold markers
                import re
                cleaned_text = message_text
                cleaned_text = re.sub(r'<!here>', '', cleaned_text)  # Remove @here
                cleaned_text = re.sub(r'<!channel>', '', cleaned_text)  # Remove @channel
                cleaned_text = re.sub(r':[a-z_]+:', '', cleaned_text)  # Remove :emoji:
                cleaned_text = re.sub(r'\*([^*]+):\*', '', cleaned_text)  # Remove *User:* or *Test User:*
                cleaned_text = cleaned_text.strip()  # Remove leading/trailing spaces
                
                # Determine if this is from operations team or user
                # If message contains bot_id or starts with emoji, it's from operations
                direction = "inbound" if not msg.get('bot_id') else "outbound"
                user_name = f"Ops-{user_id[:8]}" if direction == "inbound" else "User"
                
                cursor.execute("""
                    INSERT INTO slack_messages 
                    (message_id, incident_id, ticket_id, user_name, message_text, direction, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    message_id,
                    incident_id,
                    ticket_id,
                    user_name,
                    cleaned_text,  # Use cleaned text
                    direction,
                    datetime.now(timezone.utc).isoformat()
                ))
                synced_count += 1
                
                # Check if message contains "resolved" to auto-resolve incident
                if "resolved" in cleaned_text.lower() and direction == "inbound":
                    print(f"🎯 Detected 'resolved' keyword in Slack message - auto-resolving incident {incident_id}")
                    
                    # Update ticket status to resolved
                    cursor.execute("""
                        UPDATE tickets 
                        SET status = 'resolved', updated_at = ?
                        WHERE id = ?
                    """, (datetime.now(timezone.utc).isoformat(), ticket_id))
                    
                    # Update P1 incident status
                    cursor.execute("""
                        UPDATE p1_incidents 
                        SET status = 'resolved', resolved_at = ?
                        WHERE incident_id = ?
                    """, (datetime.now(timezone.utc).isoformat(), incident_id))
                    
                    print(f"✅ Incident {incident_id} auto-resolved based on Slack message")
                    
                    # Update Slack thread with resolved status
                    if slack_channel_manager:
                        try:
                            slack_channel_manager.update_incident_status(thread_ts, "resolved")
                        except Exception as slack_err:
                            print(f"⚠️ Could not update Slack thread status: {slack_err}")
            
            conn.commit()
        
        print(f"✅ Synced {synced_count} new messages from Slack")
        return {"synced": synced_count, "message": f"Synced {synced_count} messages from Slack"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Sync Slack messages error: {e}")
        raise create_error_response(f"Failed to sync messages: {str(e)}", 500)

@app.post("/api/incidents/{incident_id}/simulate-slack-reply")
async def simulate_slack_reply(incident_id: str, request: Request):
    """
    TEST ENDPOINT: Simulate receiving a message from Slack
    In production, this would come from Slack Event Subscriptions webhook
    """
    try:
        body = await request.json()
        message_text = body.get("message", "Test message from operations team")
        user_name = body.get("user_name", "Operations Team")
        
        # Get ticket_id from incident
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ticket_id FROM p1_incidents WHERE incident_id = ?", (incident_id,))
            result = cursor.fetchone()
            
            if not result:
                raise create_error_response("Incident not found", 404)
            
            ticket_id = result[0]
            
            # Store inbound message
            import time
            message_id = f"msg-inbound-{int(time.time())}-{uuid.uuid4().hex[:9]}"
            cursor.execute("""
                INSERT INTO slack_messages 
                (message_id, incident_id, ticket_id, user_name, message_text, direction, created_at)
                VALUES (?, ?, ?, ?, ?, 'inbound', ?)
            """, (
                message_id,
                incident_id,
                ticket_id,
                user_name,
                message_text,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()
        
        print(f"✅ Simulated Slack reply stored: {message_text[:50]}")
        
        return {
            "status": "success",
            "message_id": message_id,
            "message": "Simulated Slack message stored"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Simulate reply error: {e}")
        raise create_error_response(f"Failed to simulate reply: {str(e)}", 500)

@app.post("/api/slack/webhook")
async def slack_webhook(request: Request):
    """
    REAL SLACK WEBHOOK: Receives messages from Slack when operations team replies
    Configure this URL in Slack Event Subscriptions: https://your-domain.com/api/slack/webhook
    """
    try:
        body = await request.json()
        print(f"\n{'='*60}")
        print(f"📨 WEBHOOK CALLED - Type: {body.get('type')}")
        print(f"📨 Full webhook body: {json.dumps(body, indent=2)}")
        print(f"{'='*60}\n")
        
        # Handle Slack URL verification challenge
        if body.get("type") == "url_verification":
            print("✅ URL verification challenge received")
            return {"challenge": body.get("challenge")}
        
        # Handle Slack events
        if body.get("type") == "event_callback":
            event = body.get("event", {})
            print(f"🎯 Event type: {event.get('type')}")
            print(f"🤖 Bot ID: {event.get('bot_id')}")
            print(f"📝 Event data: {json.dumps(event, indent=2)}")
            
            # Only process messages (not bot messages)
            if event.get("type") == "message" and not event.get("bot_id"):
                message_text = event.get("text", "")
                user_id = event.get("user", "unknown")
                channel_id = event.get("channel", "")
                ts = event.get("ts", "")
                thread_ts = event.get("thread_ts", "")  # Get thread timestamp
                
                print(f"💬 Processing message: {message_text}")
                print(f"👤 User: {user_id}")
                print(f"📍 Channel: {channel_id}")
                print(f"🧵 Thread TS: {thread_ts}")
                
                # Find incident by thread_ts (for threaded conversations)
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    incident_id = None
                    ticket_id = None
                    
                    # If this is a thread reply, find incident by thread_ts
                    if thread_ts:
                        cursor.execute("""
                            SELECT incident_id, ticket_id 
                            FROM p1_incidents 
                            WHERE slack_thread_ts = ?
                        """, (thread_ts,))
                        result = cursor.fetchone()
                        
                        if result:
                            incident_id, ticket_id = result
                            print(f"✅ Found incident {incident_id} for thread {thread_ts}")
                    
                    # Fallback: Try to find by slack_channel_id
                    if not incident_id:
                        cursor.execute("""
                            SELECT incident_id, ticket_id 
                            FROM p1_incidents 
                            WHERE slack_channel_id = ?
                            ORDER BY created_at DESC 
                            LIMIT 1
                        """, (channel_id,))
                        result = cursor.fetchone()
                        if result:
                            incident_id, ticket_id = result
                    
                    # Last resort: Use most recent unresolved P1 incident
                    if not incident_id:
                        print(f"⚠️ No incident found for thread/channel, using most recent P1 incident")
                        cursor.execute("""
                            SELECT incident_id, ticket_id 
                            FROM p1_incidents 
                            WHERE status != 'resolved'
                            ORDER BY created_at DESC 
                            LIMIT 1
                        """)
                        result = cursor.fetchone()
                        if result:
                            incident_id, ticket_id = result
                    
                    if incident_id:
                        # Store the message
                        import time
                        message_id = f"msg-slack-{int(time.time())}-{uuid.uuid4().hex[:9]}"
                        
                        cursor.execute("""
                            INSERT INTO slack_messages 
                            (message_id, incident_id, ticket_id, user_name, message_text, direction, created_at)
                            VALUES (?, ?, ?, ?, ?, 'inbound', ?)
                        """, (
                            message_id,
                            incident_id,
                            ticket_id,
                            f"Ops-{user_id[:8]}",
                            message_text,
                            datetime.now(timezone.utc).isoformat()
                        ))
                        conn.commit()
                        
                        print(f"✅ Slack message stored for incident {incident_id}")
                        
                        # Check if message contains "resolved" keyword to auto-resolve incident
                        if "resolved" in message_text.lower():
                            print(f"🎯 Detected 'resolved' keyword - auto-resolving incident {incident_id}")
                            
                            # Update ticket status to resolved
                            cursor.execute("""
                                UPDATE tickets 
                                SET status = 'resolved', updated_at = ?
                                WHERE id = ?
                            """, (datetime.now(timezone.utc).isoformat(), ticket_id))
                            
                            # Update P1 incident status
                            cursor.execute("""
                                UPDATE p1_incidents 
                                SET status = 'resolved', resolved_at = ?
                                WHERE incident_id = ?
                            """, (datetime.now(timezone.utc).isoformat(), incident_id))
                            
                            conn.commit()
                            
                            print(f"✅ Incident {incident_id} and ticket {ticket_id} marked as resolved")
                            
                            # Add system message confirming resolution
                            resolution_message_id = f"msg-system-{int(time.time())}-{uuid.uuid4().hex[:9]}"
                            cursor.execute("""
                                INSERT INTO slack_messages 
                                (message_id, incident_id, ticket_id, user_name, message_text, direction, created_at)
                                VALUES (?, ?, ?, ?, ?, 'inbound', ?)
                            """, (
                                resolution_message_id,
                                incident_id,
                                ticket_id,
                                "System",
                                "✅ P1 Incident has been automatically resolved based on Slack confirmation.",
                                datetime.now(timezone.utc).isoformat()
                            ))
                            conn.commit()
                    else:
                        print(f"⚠️ No P1 incidents found in database")
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"❌ Slack webhook error: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

# ============================================
# Main Server Entry Point
# ============================================

# Main function for local development
def main():
    """Run the server locally"""
    print("🚀 Starting Support Portal API")
    print("=" * 50)
    print(f"📍 Server: http://localhost:{Config.PORT}")
    print(f"📚 API Docs: http://localhost:{Config.PORT}/docs")
    print(f"💾 Database: {Config.SQLITE_DB_PATH}")
    print(f"📁 Uploads: {Config.UPLOAD_FOLDER}/")
    if storage_manager.s3_client:
        print(f"☁️ S3 Bucket: {Config.S3_BUCKET_NAME}")
    else:
        print("🏠 File Storage: Local only")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=Config.PORT,
            reload=Config.DEBUG,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

# AWS Lambda handler (for future deployment)
def lambda_handler(event, context):
    """AWS Lambda handler function"""
    # This will be implemented when converting to Lambda
    pass

if __name__ == "__main__":
    main()

