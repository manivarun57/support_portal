#!/usr/bin/env python3
import sqlite3

def check_database_schema():
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("=== All Tables in Database ===")
    for table in tables:
        print(f"- {table[0]}")
    
    # Check if comments table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comments'")
    comments_table = cursor.fetchone()
    
    if comments_table:
        print("\n=== Comments Table Schema ===")
        cursor.execute("PRAGMA table_info(comments)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]}")
        
        # Check comment count
        cursor.execute("SELECT COUNT(*) FROM comments")
        count = cursor.fetchone()[0]
        print(f"\nTotal comments in table: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, ticket_id, user_id, comment, created_at FROM comments LIMIT 3")
            sample_comments = cursor.fetchall()
            print("\n=== Sample Comments ===")
            for comment in sample_comments:
                print(f"ID: {comment[0][:8]}...")
                print(f"Ticket: {comment[1][:8]}...")
                print(f"User: {comment[2]}")
                print(f"Comment: {comment[3][:50]}...")
                print(f"Created: {comment[4]}")
                print("-" * 30)
    else:
        print("\n❌ Comments table does not exist!")
    
    conn.close()

if __name__ == "__main__":
    check_database_schema()