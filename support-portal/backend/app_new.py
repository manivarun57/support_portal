#!/usr/bin/env python3
"""
Support Portal API - Main Application
FastAPI backend with modular P1 incident management

This file contains the main FastAPI application with standard ticket endpoints.
P1 incident functionality is in p1_incidents_api.py
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

# FastAPI imports
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

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import shared components
from shared import (
    Config, DatabaseManager, StorageManager, TicketRepository,
    create_error_response, ApiResponse, Ticket
)

# Ensure upload folder exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Additional Data Models (not in shared)
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

# API Request Models
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
    """Extended TicketRepository with additional methods for the main app"""
    
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

class CommentRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_comments(self, ticket_id: str) -> List[Dict]:
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

class TicketFileRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_ticket_file(self, ticket_id: str, file_url: str, file_name: str) -> str:
        """Create a ticket file record"""
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
ticket_repo = ExtendedTicketRepository(db_manager)
comment_repo = CommentRepository(db_manager)
file_repo = TicketFileRepository(db_manager)

# FastAPI app
app = FastAPI(
    title="Support Portal API",
    description="FastAPI backend for support ticket management with P1 incident support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility Functions
def create_error_response(message: str, status_code: int = 400):
    return HTTPException(status_code=status_code, detail={"success": False, "message": message})

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Support Portal API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/tickets")
async def create_ticket(request: CreateTicketRequest):
    """Create a new support ticket"""
    try:
        attachment_url = None
        
        # Handle file attachment if provided
        if request.attachment and request.attachment_name:
            try:
                file_url, file_size = storage_manager.upload_file(
                    request.attachment,
                    request.attachment_name,
                    request.attachment_type or 'application/octet-stream'
                )
                attachment_url = file_url
            except Exception as file_error:
                print(f"⚠️ File upload failed: {file_error}")
                # Continue without attachment rather than failing the whole request
        
        # Create the ticket
        ticket = ticket_repo.create_ticket(
            subject=request.subject,
            priority=request.priority,
            category=request.category,
            description=request.description,
            user_id=Config.DEFAULT_USER_ID,
            attachment_url=attachment_url
        )
        
        return ApiResponse(
            success=True,
            message="Ticket created successfully",
            data=asdict(ticket)
        )
    
    except Exception as e:
        print(f"❌ Create ticket error: {e}")
        raise create_error_response(f"Failed to create ticket: {str(e)}", 500)

@app.get("/tickets/my")
async def get_my_tickets(user_id: str = Config.DEFAULT_USER_ID):
    """Get all tickets for the current user"""
    try:
        tickets = ticket_repo.get_my_tickets(user_id)
        return ApiResponse(
            success=True,
            message=f"Found {len(tickets)} tickets",
            data={"tickets": tickets}
        )
    except Exception as e:
        print(f"❌ Get tickets error: {e}")
        raise create_error_response(f"Failed to fetch tickets: {str(e)}", 500)

@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID"""
    try:
        ticket = ticket_repo.get_ticket(ticket_id)
        if not ticket:
            raise create_error_response("Ticket not found", 404)
        
        return ApiResponse(
            success=True,
            message="Ticket found",
            data=ticket
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get ticket error: {e}")
        raise create_error_response(f"Failed to fetch ticket: {str(e)}", 500)

@app.get("/tickets/{ticket_id}/comments")
async def get_ticket_comments(ticket_id: str):
    """Get all comments for a ticket"""
    try:
        comments = comment_repo.get_comments(ticket_id)
        return ApiResponse(
            success=True,
            message=f"Found {len(comments)} comments",
            data={"comments": comments}
        )
    except Exception as e:
        print(f"❌ Get comments error: {e}")
        raise create_error_response(f"Failed to fetch comments: {str(e)}", 500)

@app.get("/dashboard/metrics")
async def get_dashboard_metrics():
    """Get dashboard metrics and statistics"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get ticket counts by status
            cursor.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            # Get total ticket count
            cursor.execute("SELECT COUNT(*) FROM tickets")
            total_tickets = cursor.fetchone()[0]
        
        return ApiResponse(
            success=True,
            message="Dashboard metrics retrieved",
            data={
                "total_tickets": total_tickets,
                "status_breakdown": status_counts,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"❌ Get metrics error: {e}")
        raise create_error_response(f"Failed to fetch metrics: {str(e)}", 500)

# Import P1 Incident API routes
try:
    from p1_incidents_api import router as p1_router, init_p1_components
    
    # Initialize P1 components with shared dependencies
    init_p1_components(db_manager, storage_manager, ticket_repo)
    
    # Include P1 incident routes
    app.include_router(p1_router)
    print("✅ P1 Incident API routes loaded successfully")
except ImportError as e:
    print(f"⚠️ P1 Incident API not available: {e}")

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
    print("🚀 Starting Support Portal API Server...")
    print(f"📊 Database: {Config.SQLITE_DB_PATH}")
    print(f"📁 Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"🌐 Server will be available at: http://localhost:{Config.PORT}")
    print(f"📚 API documentation: http://localhost:{Config.PORT}/docs")
    
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=Config.PORT,
            reload=Config.DEBUG,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()