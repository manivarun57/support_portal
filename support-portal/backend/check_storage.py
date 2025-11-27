#!/usr/bin/env python3
"""
Check database contents and storage locations
"""

import sqlite3
import os
from pathlib import Path

def check_database():
    print("🗄️ DATA STORAGE LOCATIONS")
    print("=" * 50)
    
    # Backend directory
    backend_dir = Path(__file__).parent
    print(f"📁 Backend Directory: {backend_dir.absolute()}")
    
    # Database file
    db_path = backend_dir / "support_portal.db"
    print(f"💾 Database File: {db_path}")
    print(f"   Exists: {'✅ Yes' if db_path.exists() else '❌ No'}")
    
    if db_path.exists():
        print(f"   Size: {db_path.stat().st_size} bytes")
        
        # Check database contents
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 Database Tables:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} records")
            
            # Show sample data for tickets table
            if table_name == "tickets" and count > 0:
                cursor.execute("SELECT id, subject, priority, status, created_at FROM tickets LIMIT 3")
                rows = cursor.fetchall()
                print(f"     Sample data:")
                for row in rows:
                    print(f"       ID: {row[0][:8]}... | Subject: {row[1][:30]}... | Status: {row[3]}")
        
        conn.close()
    
    # File uploads directory
    uploads_dir = backend_dir / "uploads"
    print(f"\n📁 File Uploads Directory: {uploads_dir}")
    print(f"   Exists: {'✅ Yes' if uploads_dir.exists() else '❌ No'}")
    
    if uploads_dir.exists():
        files = list(uploads_dir.glob("*"))
        print(f"   Files stored: {len(files)}")
        for file in files[:5]:  # Show first 5 files
            print(f"     - {file.name} ({file.stat().st_size} bytes)")
        if len(files) > 5:
            print(f"     ... and {len(files) - 5} more files")
    
    # Environment configuration
    env_file = backend_dir / ".env"
    print(f"\n⚙️ Configuration File: {env_file}")
    print(f"   Exists: {'✅ Yes' if env_file.exists() else '❌ No'}")
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "DATABASE_URL=" in content:
                db_url = [line for line in content.split('\n') if line.startswith('DATABASE_URL=')]
                if db_url:
                    url_value = db_url[0].split('=', 1)[1]
                    if url_value.strip():
                        print(f"   Using: PostgreSQL ({url_value[:30]}...)")
                    else:
                        print(f"   Using: SQLite (local file)")
            
            if "S3_BUCKET_NAME=" in content:
                bucket = [line for line in content.split('\n') if line.startswith('S3_BUCKET_NAME=')]
                if bucket:
                    bucket_value = bucket[0].split('=', 1)[1]
                    if bucket_value.strip():
                        print(f"   File Storage: AWS S3 ({bucket_value})")
                    else:
                        print(f"   File Storage: Local uploads/ folder")
    
    print(f"\n🔍 DATA ACCESS:")
    print(f"   - View database: Use SQLite browser tool")
    print(f"   - API access: http://localhost:8000/docs")
    print(f"   - Direct file: {db_path}")
    print(f"   - Uploaded files: {uploads_dir}")

if __name__ == "__main__":
    check_database()