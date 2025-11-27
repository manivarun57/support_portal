#!/usr/bin/env python3
"""
Shared components for the Support Portal API
Common models, utilities, and database components used by different modules
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
from dataclasses import dataclass

# FastAPI imports
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# AWS imports (optional)
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
    pass

# Configuration
class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "support_portal.db")
    
    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
    
    # File Upload
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    
    # Auth
    DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "demo-user")
    
    # Server
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Common Response Models
class ApiResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Optional[Dict[Any, Any]] = None

# Utility Functions
def create_error_response(message: str, status_code: int = 400):
    """Create a standardized error response"""
    return HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "message": message,
            "error_code": status_code
        }
    )

# Database Manager
class DatabaseManager:
    def __init__(self):
        self.db_path = Config.SQLITE_DB_PATH
        self.init_database()
    
    def get_connection(self):
        """Get database connection with fallback to SQLite"""
        # Try PostgreSQL first if DATABASE_URL is provided
        if Config.DATABASE_URL and "postgresql" in Config.DATABASE_URL:
            try:
                import psycopg2
                return psycopg2.connect(Config.DATABASE_URL)
            except Exception as e:
                print(f"⚠️ PostgreSQL connection failed, falling back to SQLite: {e}")
        
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
            print("✅ Database initialized successfully")

# Storage Manager
class StorageManager:
    def __init__(self):
        self.s3_client = None
        self.init_s3()
    
    def init_s3(self):
        """Initialize S3 client if credentials are available"""
        if HAS_BOTO3 and Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
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
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            
            file_url = f"/uploads/{unique_filename}"
            print(f"✅ File saved locally: {file_url}")
            return file_url, file_size
            
        except Exception as e:
            print(f"❌ File upload failed: {e}")
            raise HTTPException(status_code=400, detail=f"File upload failed: {str(e)}")

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

# Repository Classes
class TicketRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Get a single ticket by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, priority, category, description, status, 
                       user_id, created_at, attachment_url
                FROM tickets WHERE id = ?
            """, (ticket_id,))
            
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