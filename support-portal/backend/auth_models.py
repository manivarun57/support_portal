#!/usr/bin/env python3
"""
Authentication Models and Database Schema
Handles merchants, users, and authentication
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, List
from dataclasses import dataclass

# Database Schema
AUTH_SCHEMA = """
-- Merchants table (companies/organizations)
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL UNIQUE,
    company_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    status TEXT DEFAULT 'active',
    api_key TEXT UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- Users table (individuals within merchants)
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    last_login TEXT,
    FOREIGN KEY (merchant_id) REFERENCES merchants (merchant_id)
);

-- Sessions table (for authentication tracking)
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants (merchant_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_merchant ON users(merchant_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
"""

# Update tickets table to include merchant_id and user details
UPDATE_TICKETS_SCHEMA = """
ALTER TABLE tickets ADD COLUMN merchant_id TEXT;
ALTER TABLE tickets ADD COLUMN merchant_name TEXT;
ALTER TABLE tickets ADD COLUMN user_name TEXT;
ALTER TABLE tickets ADD COLUMN user_email TEXT;
"""

# Update p1_incidents to include merchant details
UPDATE_P1_INCIDENTS_SCHEMA = """
ALTER TABLE p1_incidents ADD COLUMN merchant_id TEXT;
ALTER TABLE p1_incidents ADD COLUMN merchant_name TEXT;
ALTER TABLE p1_incidents ADD COLUMN user_name TEXT;
"""

@dataclass
class Merchant:
    merchant_id: str
    merchant_name: str
    company_name: str
    email: str
    phone: Optional[str]
    status: str
    api_key: str
    created_at: str
    updated_at: Optional[str] = None

@dataclass
class User:
    user_id: str
    merchant_id: str
    username: str
    email: str
    full_name: str
    role: str
    status: str
    created_at: str
    last_login: Optional[str] = None

@dataclass
class Session:
    session_id: str
    user_id: str
    merchant_id: str
    token: str
    created_at: str
    expires_at: str


class AuthManager:
    """Handles authentication and user management"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Initialize authentication tables"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create auth tables
            cursor.executescript(AUTH_SCHEMA)
            
            # Try to add columns to tickets table (ignore if already exists)
            try:
                cursor.execute("ALTER TABLE tickets ADD COLUMN merchant_id TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE tickets ADD COLUMN merchant_name TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE tickets ADD COLUMN user_name TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE tickets ADD COLUMN user_email TEXT")
            except:
                pass
            
            # Update p1_incidents table
            try:
                cursor.execute("ALTER TABLE p1_incidents ADD COLUMN merchant_id TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE p1_incidents ADD COLUMN merchant_name TEXT")
            except:
                pass
            
            try:
                cursor.execute("ALTER TABLE p1_incidents ADD COLUMN user_name TEXT")
            except:
                pass
            
            conn.commit()
            print("✅ Authentication tables initialized")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate unique API key for merchant"""
        return f"mk_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate session token"""
        return secrets.token_urlsafe(48)
    
    def create_merchant(self, merchant_name: str, company_name: str, 
                       email: str, phone: str = None) -> Merchant:
        """Create a new merchant"""
        merchant_id = f"merchant_{uuid.uuid4().hex[:12]}"
        api_key = self.generate_api_key()
        created_at = datetime.now(timezone.utc).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO merchants 
                (merchant_id, merchant_name, company_name, email, phone, api_key, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """, (merchant_id, merchant_name, company_name, email, phone, api_key, created_at))
            conn.commit()
        
        return Merchant(
            merchant_id=merchant_id,
            merchant_name=merchant_name,
            company_name=company_name,
            email=email,
            phone=phone,
            status='active',
            api_key=api_key,
            created_at=created_at
        )
    
    def create_user(self, merchant_id: str, username: str, email: str, 
                   password: str, full_name: str, role: str = 'user') -> User:
        """Create a new user under a merchant"""
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        password_hash = self.hash_password(password)
        created_at = datetime.now(timezone.utc).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users 
                (user_id, merchant_id, username, email, password_hash, full_name, role, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (user_id, merchant_id, username, email, password_hash, full_name, role, created_at))
            conn.commit()
        
        return User(
            user_id=user_id,
            merchant_id=merchant_id,
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            status='active',
            created_at=created_at
        )
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user + merchant info"""
        password_hash = self.hash_password(password)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.user_id, u.merchant_id, u.username, u.email, u.full_name, 
                       u.role, u.status, m.merchant_name, m.company_name
                FROM users u
                JOIN merchants m ON u.merchant_id = m.merchant_id
                WHERE u.username = ? AND u.password_hash = ? AND u.status = 'active'
            """, (username, password_hash))
            
            row = cursor.fetchone()
            if row:
                # Update last login
                cursor.execute("""
                    UPDATE users SET last_login = ? WHERE user_id = ?
                """, (datetime.now(timezone.utc).isoformat(), row[0]))
                conn.commit()
                
                return {
                    'user_id': row[0],
                    'merchant_id': row[1],
                    'username': row[2],
                    'email': row[3],
                    'full_name': row[4],
                    'role': row[5],
                    'status': row[6],
                    'merchant_name': row[7],
                    'company_name': row[8]
                }
        
        return None
    
    def create_session(self, user_id: str, merchant_id: str) -> str:
        """Create a new session and return token"""
        session_id = str(uuid.uuid4())
        token = self.generate_session_token()
        created_at = datetime.now(timezone.utc).isoformat()
        
        # Session expires in 7 days
        from datetime import timedelta
        expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, merchant_id, token, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, merchant_id, token, created_at, expires_at))
            conn.commit()
        
        return token
    
    def verify_session(self, token: str) -> Optional[Dict]:
        """Verify session token and return user + merchant info"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.user_id, s.merchant_id, s.expires_at,
                       u.username, u.email, u.full_name, u.role,
                       m.merchant_name, m.company_name
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                JOIN merchants m ON s.merchant_id = m.merchant_id
                WHERE s.token = ? AND u.status = 'active'
            """, (token,))
            
            row = cursor.fetchone()
            if row:
                # Check if session expired
                expires_at = datetime.fromisoformat(row[2])
                if expires_at < datetime.now(timezone.utc):
                    return None  # Session expired
                
                return {
                    'user_id': row[0],
                    'merchant_id': row[1],
                    'username': row[3],
                    'email': row[4],
                    'full_name': row[5],
                    'role': row[6],
                    'merchant_name': row[7],
                    'company_name': row[8]
                }
        
        return None
    
    def get_merchant(self, merchant_id: str) -> Optional[Dict]:
        """Get merchant by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT merchant_id, merchant_name, company_name, email, phone, status, api_key, created_at
                FROM merchants WHERE merchant_id = ?
            """, (merchant_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'merchant_id': row[0],
                    'merchant_name': row[1],
                    'company_name': row[2],
                    'email': row[3],
                    'phone': row[4],
                    'status': row[5],
                    'api_key': row[6],
                    'created_at': row[7]
                }
        return None
    
    def get_users_by_merchant(self, merchant_id: str) -> List[Dict]:
        """Get all users for a merchant"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, email, full_name, role, status, created_at, last_login
                FROM users WHERE merchant_id = ?
                ORDER BY created_at DESC
            """, (merchant_id,))
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'full_name': row[3],
                    'role': row[4],
                    'status': row[5],
                    'created_at': row[6],
                    'last_login': row[7]
                })
            return users
