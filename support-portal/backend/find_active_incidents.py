#!/usr/bin/env python3
"""
Find the latest active P1 incidents with their Slack thread info
"""
import sqlite3

conn = sqlite3.connect('support_portal.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT p.incident_id, p.slack_thread_ts, p.created_at, t.subject
    FROM p1_incidents p
    JOIN tickets t ON p.ticket_id = t.id
    WHERE p.status = 'active'
    ORDER BY p.created_at DESC
    LIMIT 10
""")

incidents = cursor.fetchall()

print("=" * 80)
print("LATEST ACTIVE P1 INCIDENTS")
print("=" * 80)

for i, (incident_id, thread_ts, created_at, subject) in enumerate(incidents, 1):
    print(f"\n{i}. Incident: {incident_id}")
    print(f"   Subject: {subject}")
    print(f"   Thread TS: {thread_ts}")
    print(f"   Created: {created_at}")
    
    # Convert thread_ts to readable timestamp
    if thread_ts:
        import datetime
        ts_seconds = float(thread_ts.split('.')[0])
        dt = datetime.datetime.fromtimestamp(ts_seconds)
        print(f"   📅 Thread created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

conn.close()

print("\n" + "=" * 80)
print("TIP: The thread_ts matches the Slack message timestamp")
print("In Slack, look for messages posted at the times shown above")
print("=" * 80)
