#!/usr/bin/env python3
"""
Simplified Support Portal Backend - Fixed Version
This version focuses on stability and proper error handling
"""

import os
import sys
import uuid
import base64
import sqlite3
import traceback
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

# FastAPI imports
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configuration
class Config:
    SQLITE_DB_PATH = "support_portal.db"
    UPLOAD_FOLDER = "uploads"
    MAX_FILE_SIZE = 10485760  # 10MB
    DEFAULT_USER_ID = "demo-user"
    PORT = 8000

# Ensure upload folder exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Data Models
@dataclass
class Ticket:
    id: str
    subject: str
    priority: str
    category: str
    description: str
    status: str
    user_id: str
    created_at: str
    attachment_url: Optional[str] = None

# Pydantic models
class CreateTicketRequest(BaseModel):
    subject: str
    priority: str
    category: str
    description: str
    attachment: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None

# Database Manager
class DatabaseManager:
    def __init__(self):
        self.db_path = Config.SQLITE_DB_PATH
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        try:
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
                print("✅ Database initialized")
        except Exception as e:
            print(f"❌ Database error: {e}")

# Repository
class TicketRepository:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_ticket(self, subject: str, priority: str, category: str, 
                     description: str, user_id: str) -> Ticket:
        ticket_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tickets (id, subject, priority, category, description, 
                                   status, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, 'open', ?, ?)
            """, (ticket_id, subject, priority, category, description, user_id, created_at))
            conn.commit()
        
        return Ticket(
            id=ticket_id,
            subject=subject,
            priority=priority,
            category=category,
            description=description,
            status='open',
            user_id=user_id,
            created_at=created_at
        )
    
    def get_my_tickets(self, user_id: str) -> List[Dict]:
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
    
    def get_dashboard_metrics(self, user_id: str) -> Dict[str, int]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total tickets
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ?", (user_id,))
            total = cursor.fetchone()[0]
            
            # Open tickets  
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND status IN ('open', 'in_progress')", (user_id,))
            open_tickets = cursor.fetchone()[0]
            
            # Resolved tickets
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND status IN ('resolved', 'closed')", (user_id,))
            resolved = cursor.fetchone()[0]
            
            return {
                'total': total,
                'open': open_tickets, 
                'resolved': resolved
            }

class CommentRepository:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_comments_for_ticket(self, ticket_id: str) -> List[Dict]:
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

# Initialize
db_manager = DatabaseManager()
ticket_repo = TicketRepository(db_manager)
comment_repo = CommentRepository(db_manager)

# FastAPI app
app = FastAPI(
    title="Support Portal API",
    version="1.0.0",
    docs_url="/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def get_user_id(request: Request) -> str:
    user_id = request.headers.get("X-User-Id") or Config.DEFAULT_USER_ID
    return user_id

# Routes
@app.get("/")
def root():
    return {"message": "Support Portal API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/tickets")
async def create_ticket(request: Request, ticket_data: CreateTicketRequest):
    try:
        user_id = get_user_id(request)
        
        # Validate priority
        if ticket_data.priority not in ["low", "medium", "high"]:
            raise HTTPException(status_code=400, detail="Invalid priority")
        
        ticket = ticket_repo.create_ticket(
            subject=ticket_data.subject,
            priority=ticket_data.priority,
            category=ticket_data.category,
            description=ticket_data.description,
            user_id=user_id
        )
        
        print(f"✅ Ticket created: {ticket.id}")
        return {"ticket": asdict(ticket)}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create ticket error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ticket")

@app.get("/tickets/my")
async def get_my_tickets(request: Request):
    try:
        user_id = get_user_id(request)
        tickets = ticket_repo.get_my_tickets(user_id)
        print(f"✅ Fetched {len(tickets)} tickets for {user_id}")
        return {"tickets": tickets}
        
    except Exception as e:
        print(f"❌ Get tickets error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tickets")

@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, request: Request):
    try:
        user_id = get_user_id(request)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, priority, category, description, status, 
                       user_id, created_at, attachment_url
                FROM tickets WHERE id = ? AND user_id = ?
            """, (ticket_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Ticket not found")
            
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
            
            return {"ticket": ticket}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get ticket error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ticket")

@app.get("/tickets/{ticket_id}/comments")
async def get_ticket_comments(ticket_id: str):
    try:
        comments = comment_repo.get_comments_for_ticket(ticket_id)
        return {"comments": comments}
        
    except Exception as e:
        print(f"❌ Get comments error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch comments")

@app.get("/dashboard/metrics")
async def get_dashboard_metrics(request: Request):
    try:
        user_id = get_user_id(request)
        metrics = ticket_repo.get_dashboard_metrics(user_id)
        print(f"✅ Metrics for {user_id}: {metrics}")
        return {"metrics": metrics}
        
    except Exception as e:
        print(f"❌ Get metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"❌ Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )