#!/usr/bin/env python3
"""
Migrate old P1 incident to use Slack threading
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

def migrate_old_incident():
    """Create a thread for the old P1 incident"""
    
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("❌ Slack credentials not found!")
        return
    
    # Connect to database
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    # Get the old incident
    incident_id = "P1-20251201-A3715B5B"
    cursor.execute('''
        SELECT incident_id, ticket_id, slack_thread_ts, status
        FROM p1_incidents
        WHERE incident_id = ?
    ''', (incident_id,))
    
    incident = cursor.fetchone()
    if not incident:
        print(f"❌ Incident {incident_id} not found!")
        conn.close()
        return
    
    incident_id, ticket_id, current_thread_ts, status = incident
    
    print(f"📋 Found incident: {incident_id}")
    print(f"   Ticket ID: {ticket_id}")
    print(f"   Current thread_ts: {current_thread_ts}")
    print(f"   Status: {status}")
    
    if current_thread_ts:
        print(f"\n✅ Incident already has a thread: {current_thread_ts}")
        conn.close()
        return
    
    # Get ticket details
    cursor.execute('''
        SELECT id, subject, description, priority, category, status, created_at, user_id
        FROM tickets
        WHERE id = ?
    ''', (ticket_id,))
    
    ticket = cursor.fetchone()
    if not ticket:
        print(f"❌ Ticket {ticket_id} not found!")
        conn.close()
        return
    
    # Create Slack thread for this incident
    print(f"\n🚀 Creating Slack thread for old incident...")
    
    manager = SlackChannelManager(SLACK_BOT_TOKEN, SLACK_CHANNEL_ID)
    
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
            
            print(f"✅ Thread created successfully!")
            print(f"   Thread TS: {thread_ts}")
            print(f"\n🎉 Old incident can now use bidirectional messaging!")
            print(f"   Reply in the Slack thread to test it!")
        else:
            print(f"❌ Failed to create thread")
    
    except Exception as e:
        print(f"❌ Error creating thread: {e}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATE OLD P1 INCIDENT TO SLACK THREADING")
    print("=" * 60)
    migrate_old_incident()
