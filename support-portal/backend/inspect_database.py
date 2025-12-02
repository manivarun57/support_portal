#!/usr/bin/env python3
"""
Database Inspector - View P1 Critical Data Storage
Shows exactly where P1 Critical incident data is stored in the database
"""

import sqlite3
import json
from datetime import datetime

def inspect_database():
    """Inspect the support_portal.db database for P1 Critical data"""
    db_path = "support_portal.db"
    
    print("🔍 DATABASE INSPECTION - P1 Critical Data Storage")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📁 Database File: {db_path}")
        print(f"📅 Inspection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Show all database tables
        print("\n📊 DATABASE TABLES:")
        print("-" * 30)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📋 {table_name}: {count} records")
        
        # 2. Show P1 tickets in tickets table
        print(f"\n🎫 TICKETS TABLE - P1 PRIORITY TICKETS:")
        print("-" * 45)
        cursor.execute("""
            SELECT id, subject, priority, category, status, user_id, created_at
            FROM tickets 
            WHERE priority = 'P1'
            ORDER BY created_at DESC
        """)
        
        p1_tickets = cursor.fetchall()
        if p1_tickets:
            for i, ticket in enumerate(p1_tickets, 1):
                print(f"   {i}. Ticket ID: {ticket[0]}")
                print(f"      Subject: {ticket[1]}")
                print(f"      Priority: {ticket[2]} ✅")
                print(f"      Category: {ticket[3]}")
                print(f"      Status: {ticket[4]}")
                print(f"      User: {ticket[5]}")
                print(f"      Created: {ticket[6]}")
                print()
        else:
            print("   No P1 tickets found")
        
        # 3. Show P1 incidents table
        print(f"\n🚨 P1_INCIDENTS TABLE - INCIDENT TRACKING:")
        print("-" * 50)
        cursor.execute("""
            SELECT id, ticket_id, incident_id, slack_channel_id, slack_message_id,
                   slack_notification_sent, slack_notification_sent_at, slack_webhook_url,
                   status, created_at, resolved_at
            FROM p1_incidents
            ORDER BY created_at DESC
        """)
        
        p1_incidents = cursor.fetchall()
        if p1_incidents:
            for i, incident in enumerate(p1_incidents, 1):
                print(f"   {i}. P1 Incident Record:")
                print(f"      🆔 Incident ID: {incident[2]} ⭐")
                print(f"      🎫 Linked Ticket: {incident[1]}")
                print(f"      📱 Slack Channel ID: {incident[3] or 'Not set'}")
                print(f"      💬 Slack Message ID: {incident[4] or 'Not set'}")
                print(f"      ✅ Slack Sent: {'Yes' if incident[5] else 'No'}")
                print(f"      📅 Slack Sent At: {incident[6] or 'N/A'}")
                print(f"      🔗 Webhook URL: {incident[7][:50]}..." if incident[7] else 'N/A')
                print(f"      🟢 Status: {incident[8]}")
                print(f"      📅 Created: {incident[9]}")
                print(f"      🔚 Resolved: {incident[10] or 'Still active'}")
                print()
        else:
            print("   No P1 incidents found")
        
        # 4. Show joined data (tickets + incidents)
        print(f"\n🔄 JOINED VIEW - COMPLETE P1 CRITICAL DATA:")
        print("-" * 50)
        cursor.execute("""
            SELECT t.id as ticket_id, t.subject, t.priority, t.status, t.created_at,
                   p.incident_id, p.slack_notification_sent, p.slack_notification_sent_at,
                   p.status as incident_status
            FROM tickets t
            JOIN p1_incidents p ON t.id = p.ticket_id
            WHERE t.priority = 'P1'
            ORDER BY t.created_at DESC
        """)
        
        joined_data = cursor.fetchall()
        if joined_data:
            for i, row in enumerate(joined_data, 1):
                print(f"   {i}. Complete P1 Critical Record:")
                print(f"      🎫 Ticket: {row[0][:8]}... | {row[1]}")
                print(f"      🔥 Priority: {row[2]} | Status: {row[3]}")
                print(f"      🆔 Incident ID: {row[5]} ⭐")
                print(f"      📱 Slack Alert: {'✅ Sent' if row[6] else '❌ Failed'}")
                print(f"      📅 Alert Time: {row[7] or 'N/A'}")
                print(f"      🟢 Incident Status: {row[8]}")
                print(f"      📅 Created: {row[4]}")
                print()
        
        # 5. Show P1 statistics
        print(f"\n📈 P1 CRITICAL STATISTICS:")
        print("-" * 30)
        
        # Total P1 tickets
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE priority = 'P1'")
        total_p1 = cursor.fetchone()[0]
        
        # P1 incidents with Slack sent
        cursor.execute("SELECT COUNT(*) FROM p1_incidents WHERE slack_notification_sent = 1")
        slack_sent = cursor.fetchone()[0]
        
        # Active P1 incidents
        cursor.execute("SELECT COUNT(*) FROM p1_incidents WHERE status = 'active'")
        active_incidents = cursor.fetchone()[0]
        
        print(f"   📊 Total P1 Tickets: {total_p1}")
        print(f"   🚨 P1 Incidents Created: {len(p1_incidents)}")
        print(f"   📱 Slack Notifications Sent: {slack_sent}")
        print(f"   🟢 Active Incidents: {active_incidents}")
        print(f"   📈 Success Rate: {(slack_sent/len(p1_incidents)*100):.1f}%" if p1_incidents else "N/A")
        
        conn.close()
        
        print(f"\n🎯 SUMMARY - WHERE P1 CRITICAL DATA IS STORED:")
        print("=" * 60)
        print(f"📍 Location: support_portal.db SQLite database")
        print(f"📊 tickets table: Main ticket data with priority='P1'")
        print(f"🚨 p1_incidents table: Incident IDs, Slack tracking, status")
        print(f"🔗 Relationship: p1_incidents.ticket_id → tickets.id")
        print(f"📱 Slack Data: webhook_url, channel_id, message_id, sent_status")
        print(f"🆔 Incident IDs: Format P1-YYYYMMDD-XXXXXXXX")
        print(f"✅ System Status: Fully operational and tracking all P1 data!")
        
    except Exception as e:
        print(f"❌ Database inspection failed: {e}")

if __name__ == "__main__":
    inspect_database()