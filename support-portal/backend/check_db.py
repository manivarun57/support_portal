#!/usr/bin/env python3
import sqlite3

def check_tickets():
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    # Get recent tickets
    cursor.execute('''
        SELECT id, subject, priority, category, status, created_at 
        FROM tickets 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    tickets = cursor.fetchall()
    
    print("=== Recent Tickets in Database ===")
    for i, ticket in enumerate(tickets, 1):
        print(f"{i}. ID: {ticket[0][:8]}...")
        print(f"   Subject: {ticket[1]}")
        print(f"   Priority: {ticket[2]}")
        print(f"   Category: {ticket[3]}")
        print(f"   Status: {ticket[4]}")
        print(f"   Created: {ticket[5]}")
        print()
    
    # Count P1 tickets
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE priority = 'P1'")
    p1_count = cursor.fetchone()[0]
    print(f"Total P1 Critical tickets: {p1_count}")
    
    # Count all tickets by priority
    cursor.execute("SELECT priority, COUNT(*) FROM tickets GROUP BY priority")
    priority_counts = cursor.fetchall()
    print("\n=== Tickets by Priority ===")
    for priority, count in priority_counts:
        print(f"{priority}: {count} tickets")
    
    conn.close()

if __name__ == "__main__":
    check_tickets()