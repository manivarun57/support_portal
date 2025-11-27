import sqlite3
import os
import json
from datetime import datetime

# Database path
db_path = "support_portal.db"

def show_database_contents():
    """Show all data stored in the database"""
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    print("=" * 60)
    print("SUPPORT PORTAL DATABASE CONTENTS")
    print("=" * 60)
    
    # Show tickets
    print("\n📋 TICKETS:")
    print("-" * 40)
    cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    tickets = cursor.fetchall()
    
    for ticket in tickets:
        print(f"ID: {ticket['id']}")
        print(f"Subject: {ticket['subject']}")
        print(f"Description: {ticket['description']}")
        print(f"User ID: {ticket['user_id']}")
        print(f"Status: {ticket['status']}")
        print(f"Priority: {ticket['priority']}")
        print(f"Category: {ticket['category']}")
        print(f"Created: {ticket['created_at']}")
        if 'updated_at' in ticket.keys():
            print(f"Updated: {ticket['updated_at']}")
        if ticket['attachment_url']:
            print(f"Attachment: {ticket['attachment_url']}")
        print("-" * 40)
    
    # Show ticket files
    print("\n📎 TICKET FILES:")
    print("-" * 40)
    cursor.execute("SELECT * FROM ticket_files")
    files = cursor.fetchall()
    
    if files:
        for file in files:
            print(f"File ID: {file['id']}")
            print(f"Ticket ID: {file['ticket_id']}")
            print(f"Original Name: {file['original_filename']}")
            print(f"Stored Name: {file['stored_filename']}")
            print(f"File Size: {file['file_size']} bytes")
            print(f"Content Type: {file['content_type']}")
            print(f"Storage Location: {file['storage_location']}")
            print(f"S3 Key: {file['s3_key']}")
            print(f"Uploaded: {file['created_at']}")
            print("-" * 40)
    else:
        print("No files uploaded yet")
    
    # Show comments
    print("\n💬 COMMENTS:")
    print("-" * 40)
    cursor.execute("SELECT * FROM comments ORDER BY created_at")
    comments = cursor.fetchall()
    
    if comments:
        for comment in comments:
            print(f"Comment ID: {comment['id']}")
            print(f"Ticket ID: {comment['ticket_id']}")
            print(f"User ID: {comment['user_id']}")
            print(f"Content: {comment['content']}")
            print(f"Created: {comment['created_at']}")
            print("-" * 40)
    else:
        print("No comments yet")
    
    # Show database statistics
    print("\n📊 DATABASE STATISTICS:")
    print("-" * 40)
    
    cursor.execute("SELECT COUNT(*) as count FROM tickets")
    ticket_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ticket_files")
    file_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM comments")
    comment_count = cursor.fetchone()['count']
    
    print(f"Total Tickets: {ticket_count}")
    print(f"Total Files: {file_count}")
    print(f"Total Comments: {comment_count}")
    
    # Database file info
    db_size = os.path.getsize(db_path)
    print(f"Database Size: {db_size:,} bytes ({db_size / 1024:.1f} KB)")
    
    conn.close()

def show_file_storage():
    """Show file storage information"""
    uploads_dir = "uploads"
    
    print("\n📁 FILE STORAGE:")
    print("-" * 40)
    print(f"Upload Directory: {os.path.abspath(uploads_dir)}")
    
    if os.path.exists(uploads_dir):
        files = os.listdir(uploads_dir)
        if files:
            print(f"Files stored: {len(files)}")
            for file in files:
                file_path = os.path.join(uploads_dir, file)
                size = os.path.getsize(file_path)
                print(f"  - {file} ({size} bytes)")
        else:
            print("No files in uploads directory")
    else:
        print("Uploads directory doesn't exist yet")

if __name__ == "__main__":
    print("🔍 Analyzing Support Portal Data Storage...")
    show_database_contents()
    show_file_storage()
    
    print("\n" + "=" * 60)
    print("💡 HOW TO ACCESS YOUR DATA:")
    print("=" * 60)
    print("1. SQLite Database Browser: Download DB Browser for SQLite")
    print("2. Command Line: sqlite3 support_portal.db")
    print("3. Python Script: This script shows all your data")
    print("4. API Endpoints: Your FastAPI server provides REST access")
    print("\nDatabase Location:", os.path.abspath(db_path))