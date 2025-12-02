#!/usr/bin/env python3
"""
Complete diagnostic for incident P1-20251201-DDED9075
"""
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from slack_channel_manager import SlackChannelManager

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")

incident_id = "P1-20251201-DDED9075"

print("=" * 80)
print(f"COMPLETE DIAGNOSTIC FOR {incident_id}")
print("=" * 80)

# 1. Check database
conn = sqlite3.connect('support_portal.db')
cursor = conn.cursor()

print("\n1. DATABASE INFO:")
cursor.execute("""
    SELECT incident_id, ticket_id, slack_thread_ts, status, created_at
    FROM p1_incidents
    WHERE incident_id = ?
""", (incident_id,))

incident = cursor.fetchone()
if incident:
    print(f"   ✅ Incident found in database")
    print(f"   - Ticket ID: {incident[1]}")
    print(f"   - Thread TS: {incident[2]}")
    print(f"   - Status: {incident[3]}")
    print(f"   - Created: {incident[4]}")
    thread_ts = incident[2]
    ticket_id = incident[1]
else:
    print(f"   ❌ Incident not found!")
    exit(1)

# 2. Check messages in database
print("\n2. MESSAGES IN DATABASE:")
cursor.execute("""
    SELECT message_id, user_name, message_text, direction, created_at
    FROM slack_messages
    WHERE incident_id = ?
    ORDER BY created_at DESC
    LIMIT 5
""", (incident_id,))

messages = cursor.fetchall()
if messages:
    print(f"   ✅ Found {len(messages)} messages:")
    for msg in messages:
        print(f"   - [{msg[3]}] {msg[1]}: {msg[2][:50]}...")
else:
    print(f"   ⚠️ No messages found in database for this incident")

conn.close()

# 3. Check Slack thread
print("\n3. SLACK THREAD INFO:")
if thread_ts:
    manager = SlackChannelManager(SLACK_BOT_TOKEN, SLACK_CHANNEL_ID)
    
    try:
        slack_messages = manager.get_thread_replies(thread_ts)
        print(f"   ✅ Slack API accessible")
        print(f"   ✅ Found {len(slack_messages)} messages in Slack thread")
        
        if slack_messages:
            print("\n   Messages in Slack thread:")
            for i, msg in enumerate(slack_messages[:5], 1):
                user = msg.get('user', 'unknown')
                text = msg.get('text', '')[:50]
                print(f"   {i}. User {user}: {text}...")
        else:
            print("   ⚠️ Thread exists but has no replies yet")
            
    except Exception as e:
        print(f"   ❌ Error accessing Slack: {e}")
else:
    print("   ❌ No thread_ts found!")

# 4. Test sending a message
print("\n4. TEST SENDING MESSAGE:")
try:
    success = manager.post_reply(
        thread_ts=thread_ts,
        message="🧪 Diagnostic test message",
        user_name="Diagnostic"
    )
    if success:
        print("   ✅ Successfully sent test message to Slack")
    else:
        print("   ❌ Failed to send message")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
print("\nNext steps:")
print("1. Check if test message appears in Slack")
print("2. Try syncing from frontend")
print("3. Check browser console for errors")
