#!/usr/bin/env python3
"""
Quick test script for the Support Portal Backend
Tests all the main API endpoints
"""

import requests
import json
import base64
import time

API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user"

def test_api():
    print("🧪 Testing Support Portal API")
    print("=" * 40)
    
    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        print("   Make sure the backend server is running!")
        return
    
    # Test dashboard metrics
    print("2. Testing dashboard metrics...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/metrics",
            headers={"X-User-Id": TEST_USER_ID}
        )
        if response.status_code == 200:
            metrics = response.json()["metrics"]
            print(f"   ✅ Dashboard metrics: {metrics}")
        else:
            print(f"   ❌ Dashboard metrics failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Dashboard metrics error: {e}")
    
    # Test create ticket
    print("3. Testing create ticket...")
    try:
        ticket_data = {
            "subject": "Test API Ticket",
            "priority": "medium",
            "category": "testing",
            "description": "This is a test ticket created by the test script"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tickets",
            headers={
                "Content-Type": "application/json",
                "X-User-Id": TEST_USER_ID
            },
            json=ticket_data
        )
        
        if response.status_code == 200:
            ticket = response.json()["ticket"]
            ticket_id = ticket["id"]
            print(f"   ✅ Ticket created: ID {ticket_id}")
            
            # Test get my tickets
            print("4. Testing get my tickets...")
            response = requests.get(
                f"{API_BASE_URL}/tickets/my",
                headers={"X-User-Id": TEST_USER_ID}
            )
            
            if response.status_code == 200:
                tickets = response.json()["tickets"]
                print(f"   ✅ Found {len(tickets)} tickets for user")
                
                if tickets:
                    # Test get specific ticket
                    print("5. Testing get specific ticket...")
                    response = requests.get(
                        f"{API_BASE_URL}/tickets/{ticket_id}",
                        headers={"X-User-Id": TEST_USER_ID}
                    )
                    
                    if response.status_code == 200:
                        print("   ✅ Retrieved specific ticket")
                        
                        # Test get comments
                        print("6. Testing get ticket comments...")
                        response = requests.get(f"{API_BASE_URL}/tickets/{ticket_id}/comments")
                        
                        if response.status_code == 200:
                            comments = response.json()["comments"]
                            print(f"   ✅ Found {len(comments)} comments for ticket")
                        else:
                            print(f"   ❌ Get comments failed: {response.status_code}")
                    else:
                        print(f"   ❌ Get specific ticket failed: {response.status_code}")
            else:
                print(f"   ❌ Get my tickets failed: {response.status_code}")
        else:
            print(f"   ❌ Create ticket failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Create ticket error: {e}")
    
    print("\n" + "=" * 40)
    print("🎉 API Test Complete!")
    print(f"🌐 API Docs: {API_BASE_URL}/docs")
    print(f"📊 Interactive testing available at the docs URL")

if __name__ == "__main__":
    test_api()