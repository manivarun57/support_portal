#!/usr/bin/env python3
"""
Migrate ALL old P1 incidents without threads to use Slack threading
"""
import sqlite3
from slack_channel_manager import SlackChannelManager
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")

def migrate_all_incidents():
    """Create threads for all P1 incidents that don't have one"""
    
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("❌ Slack credentials not found!")
        return
    
    # Connect to database
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    # Get all incidents without thread_ts
    cursor.execute('''
        SELECT incident_id, ticket_id, status
        FROM p1_incidents
        WHERE slack_thread_ts IS NULL OR slack_thread_ts = ''
        ORDER BY created_at DESC
    ''')
    
    incidents = cursor.fetchall()
    
    if not incidents:
        print("✅ All incidents already have threads!")
        conn.close()
        return
    
    print(f"📋 Found {len(incidents)} incidents without threads")
    print("=" * 60)
    
    manager = SlackChannelManager(SLACK_BOT_TOKEN, SLACK_CHANNEL_ID)
    
    migrated_count = 0
    failed_count = 0
    
    for incident_id, ticket_id, status in incidents:
        print(f"\n🔄 Processing: {incident_id} (status: {status})")
        
        # Get ticket details
        cursor.execute('''
            SELECT id, subject, description, priority, category, status, created_at, user_id
            FROM tickets
            WHERE id = ?
        ''', (ticket_id,))
        
        ticket = cursor.fetchone()
        if not ticket:
            print(f"   ❌ Ticket {ticket_id} not found!")
            failed_count += 1
            continue
        
        # Prepare ticket data
        ticket_dict = {
            'incident_id': incident_id,
            'ticket_id': ticket[0],
            'subject': ticket[1],
            'description': ticket[2],
            'priority': ticket[3],
            'category': ticket[4],
            'status': ticket[5],
            'created_at': ticket[6],
            'merchant_name': 'Unknown',
            'user_name': 'Unknown',
            'user_email': ''
        }
        
        try:
            thread_ts = manager.post_incident(ticket_dict)
            
            if thread_ts:
                # Update database with thread_ts
                cursor.execute('''
                    UPDATE p1_incidents
                    SET slack_thread_ts = ?
                    WHERE incident_id = ?
                ''', (thread_ts, incident_id))
                conn.commit()
                
                print(f"   ✅ Thread created: {thread_ts}")
                migrated_count += 1
            else:
                print(f"   ❌ Failed to create thread")
                failed_count += 1
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed_count += 1
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Migration complete!")
    print(f"   Migrated: {migrated_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total: {len(incidents)}")

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATE ALL P1 INCIDENTS TO SLACK THREADING")
    print("=" * 60)
    migrate_all_incidents()
