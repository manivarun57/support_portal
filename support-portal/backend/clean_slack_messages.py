#!/usr/bin/env python3
"""
Clean up existing slack messages by removing Slack formatting
"""
import sqlite3
import re

def clean_slack_text(text):
    """Remove Slack formatting from message text"""
    cleaned = text
    cleaned = re.sub(r'<!here>', '', cleaned)  # Remove @here
    cleaned = re.sub(r'<!channel>', '', cleaned)  # Remove @channel
    cleaned = re.sub(r':[a-z_]+:', '', cleaned)  # Remove :emoji:
    cleaned = re.sub(r'\*([^*]+):\*', '', cleaned)  # Remove *User:* or *Test User:*
    cleaned = cleaned.strip()  # Remove leading/trailing spaces
    return cleaned

conn = sqlite3.connect('support_portal.db')
cursor = conn.cursor()

# Get all messages
cursor.execute("SELECT message_id, message_text FROM slack_messages")
messages = cursor.fetchall()

print("=" * 60)
print(f"CLEANING {len(messages)} SLACK MESSAGES")
print("=" * 60)

updated = 0
for message_id, message_text in messages:
    cleaned = clean_slack_text(message_text)
    
    if cleaned != message_text:
        cursor.execute("""
            UPDATE slack_messages
            SET message_text = ?
            WHERE message_id = ?
        """, (cleaned, message_id))
        updated += 1
        print(f"\n✅ Cleaned: {message_id}")
        print(f"   Before: {message_text[:60]}")
        print(f"   After:  {cleaned[:60]}")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print(f"✅ Updated {updated} messages")
print("=" * 60)
