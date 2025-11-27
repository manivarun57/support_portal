#!/usr/bin/env python3
"""
Database migration script to update p1_incidents table
Makes ticket_id column nullable
"""

import sqlite3
import os

def migrate_database():
    db_path = "support_portal.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if p1_incidents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='p1_incidents'")
        if cursor.fetchone():
            print("P1 incidents table exists, updating schema...")
            
            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS p1_incidents_new (
                    id TEXT PRIMARY KEY,
                    ticket_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'P1',
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    client_user_id TEXT NOT NULL,
                    assigned_admin_user_id TEXT,
                    slack_channel_id TEXT,
                    slack_channel_name TEXT,
                    incident_commander TEXT,
                    business_impact TEXT,
                    technical_details TEXT,
                    resolution_steps TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    resolved_at TEXT
                )
            """)
            
            # Copy data from old table to new table
            cursor.execute("""
                INSERT INTO p1_incidents_new 
                SELECT * FROM p1_incidents
            """)
            
            # Drop old table and rename new table
            cursor.execute("DROP TABLE p1_incidents")
            cursor.execute("ALTER TABLE p1_incidents_new RENAME TO p1_incidents")
            
            print("✅ P1 incidents table schema updated successfully")
        else:
            print("P1 incidents table doesn't exist, will be created with new schema")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()