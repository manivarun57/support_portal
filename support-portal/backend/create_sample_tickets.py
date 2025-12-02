#!/usr/bin/env python3
"""
Script to create sample tickets for different users to test user filtering
"""

import requests
import json
import time

def create_sample_tickets():
    """Create sample tickets for different users"""
    
    url = "http://localhost:8000/tickets"
    
    # Sample tickets for different users
    tickets_data = [
        {
            "user_id": "demo-user",
            "tickets": [
                {
                    "subject": "Password reset not working",
                    "priority": "medium",
                    "category": "Account Access",
                    "description": "I'm unable to reset my password. The reset email never arrives."
                },
                {
                    "subject": "VPN connection issues",
                    "priority": "high", 
                    "category": "Network",
                    "description": "Can't connect to company VPN from home office. Getting timeout errors."
                }
            ]
        },
        {
            "user_id": "john.doe",
            "tickets": [
                {
                    "subject": "Marketing campaign analytics broken",
                    "priority": "high",
                    "category": "Analytics",
                    "description": "The marketing dashboard is showing incorrect conversion rates for Q4 campaign."
                },
                {
                    "subject": "Budget approval workflow stuck",
                    "priority": "medium",
                    "category": "Workflow",
                    "description": "The budget approval for our new ad campaign has been stuck in pending for 2 weeks."
                },
                {
                    "subject": "Customer data export failing", 
                    "priority": "low",
                    "category": "Data Export",
                    "description": "Trying to export customer segment data but getting CSV generation errors."
                }
            ]
        },
        {
            "user_id": "jane.smith",
            "tickets": [
                {
                    "subject": "Critical payment gateway outage",
                    "priority": "P1",
                    "category": "P1 Critical Incident", 
                    "description": "Payment processing is completely down. All transactions failing with 500 errors. Revenue impact is significant."
                },
                {
                    "subject": "Database performance degradation",
                    "priority": "high",
                    "category": "Database",
                    "description": "Query response times have increased 400% over the past hour. Customer dashboard loading very slowly."
                },
                {
                    "subject": "SSL certificate expiring soon",
                    "priority": "medium", 
                    "category": "Security",
                    "description": "Our main domain SSL certificate expires in 7 days. Need to renew and update."
                }
            ]
        },
        {
            "user_id": "admin",
            "tickets": [
                {
                    "subject": "Server migration planning",
                    "priority": "low",
                    "category": "Infrastructure",
                    "description": "Need to plan the migration of legacy servers to cloud infrastructure."
                }
            ]
        },
        {
            "user_id": "sarah.chen", 
            "tickets": [
                {
                    "subject": "API rate limiting issues",
                    "priority": "high",
                    "category": "API",
                    "description": "Third-party API calls are being rate limited. Need to implement better retry logic."
                },
                {
                    "subject": "Code review process improvement",
                    "priority": "low",
                    "category": "Development",
                    "description": "Looking to streamline our code review process to reduce merge time."
                }
            ]
        }
    ]
    
    created_count = 0
    
    print("🎯 Creating sample tickets for user filtering test...")
    print("=" * 60)
    
    for user_data in tickets_data:
        user_id = user_data["user_id"]
        print(f"\n👤 Creating tickets for user: {user_id}")
        
        for i, ticket in enumerate(user_data["tickets"], 1):
            try:
                headers = {
                    "Content-Type": "application/json",
                    "X-User-Id": user_id
                }
                
                response = requests.post(url, json=ticket, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    response_data = response.json()
                    ticket_id = response_data.get('ticket', {}).get('id', 'unknown')[:8]
                    priority = ticket.get('priority', 'unknown')
                    
                    print(f"   ✅ [{i}] {ticket['subject'][:40]}... ({priority}) - ID: {ticket_id}")
                    
                    # Special handling for P1 tickets
                    if 'p1_incident' in response_data:
                        incident_id = response_data['p1_incident'].get('incident_id', 'unknown')
                        print(f"       🚨 P1 Incident Created: {incident_id}")
                    
                    created_count += 1
                    
                else:
                    print(f"   ❌ Failed to create ticket: {response.status_code} - {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Error creating ticket: {str(e)}")
            
            # Small delay between requests
            time.sleep(0.2)
    
    print("\n" + "=" * 60)
    print(f"✅ Sample ticket creation complete!")
    print(f"📊 Created {created_count} tickets across {len(tickets_data)} users")
    print("\n🔍 Test user filtering by:")
    print("   1. Go to the frontend (http://localhost:3000)")
    print("   2. Use the User Selector dropdown in the sidebar")
    print("   3. Switch between users to see their specific tickets")
    print("   4. Verify each user only sees their own tickets")

if __name__ == "__main__":
    try:
        create_sample_tickets()
    except KeyboardInterrupt:
        print("\n👋 Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")