#!/usr/bin/env python3
"""
List all P1 incidents and check their thread status
"""
import sqlite3

conn = sqlite3.connect('support_portal.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT incident_id, ticket_id, status, slack_thread_ts, created_at
    FROM p1_incidents
    ORDER BY created_at DESC
    LIMIT 10
""")

incidents = cursor.fetchall()

print("=" * 80)
print("ALL P1 INCIDENTS IN DATABASE")
print("=" * 80)

for incident in incidents:
    incident_id, ticket_id, status, thread_ts, created_at = incident
    print(f"\n📋 Incident: {incident_id}")
    print(f"   Ticket: {ticket_id[:13]}...")
    print(f"   Status: {status}")
    print(f"   Thread TS: {thread_ts if thread_ts else '❌ NO THREAD'}")
    print(f"   Created: {created_at}")

conn.close()
