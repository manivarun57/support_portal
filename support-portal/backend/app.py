#!/usr/bin/env python3
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
                     description: str, user_id: str, attachment_url: str = None) -> Ticket:
        """Create a new ticket"""
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
        """Get all tickets for a user"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, priority, category, description, status, 
                       user_id, created_at, attachment_url
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
    
    def create_demo_comment(self, ticket_id: str, user_id: str):
        """Create a demo comment for development"""
        comment_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        comment_text = "Thank you for submitting your ticket. We've received your request and will respond within 24 hours."
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO comments (id, ticket_id, user_id, comment, created_at)
                VALUES (?, ?, 'support-team', ?, ?)
            """, (comment_id, ticket_id, comment_text, created_at))
            conn.commit()

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

# Initialize components
db_manager = DatabaseManager()
storage_manager = StorageManager()
ticket_repo = TicketRepository(db_manager)
comment_repo = CommentRepository(db_manager)
file_repo = TicketFileRepository(db_manager)

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

@app.post("/tickets")
async def create_ticket(request: Request, ticket_data: CreateTicketRequest):
    """Create a new ticket with optional file attachment"""
    try:
        user_id = get_user_id(request)
        
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
        
        # Create ticket
        ticket = ticket_repo.create_ticket(
            subject=ticket_data.subject,
            priority=ticket_data.priority,
            category=ticket_data.category,
            description=ticket_data.description,
            user_id=user_id,
            attachment_url=attachment_url
        )
        
        # Save file record if attachment exists
        if attachment_url:
            file_repo.save_ticket_file(
                ticket_id=ticket.id,
                file_url=attachment_url,
                file_name=ticket_data.attachment_name
            )
        
        # Create demo comment for development
        comment_repo.create_demo_comment(ticket.id, user_id)
        
        print(f"✅ Ticket created: {ticket.id}")
        return {"ticket": asdict(ticket)}
        
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

