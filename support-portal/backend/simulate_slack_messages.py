"""
Quick Test Script - Simulate Slack Messages Without ngrok
This allows you to test receiving messages from Slack operations team
without needing to set up ngrok
"""

import requests
import json

# Get the incident ID you want to test
incident_id = input("Enter the P1 Incident ID (e.g., P1-20251201-60CA6134): ").strip()

if not incident_id:
    print("❌ No incident ID provided")
    exit(1)

print(f"\n🧪 Simulating Slack messages for incident: {incident_id}")
print("=" * 80)

# Test messages to simulate
test_messages = [
    {"message": "We are investigating the issue", "user_id": "U0A0KGS6"},
    {"message": "Working on the fix now", "user_id": "U0A0KGS6"},
    {"message": "resolved", "user_id": "U0A0KGS6"},  # This will auto-resolve
]

for i, msg in enumerate(test_messages, 1):
    print(f"\n{i}. Simulating message: '{msg['message']}'")
    
    try:
        response = requests.post(
            f"http://localhost:8000/api/incidents/{incident_id}/simulate-slack-reply",
            json={
                "message": msg["message"],
                "user_id": msg["user_id"]
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print(f"   ✅ Message added successfully")
            data = response.json()
            print(f"   Response: {data.get('message', '')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   Make sure backend is running on port 8000")
        break

print("\n" + "=" * 80)
print("✅ Done! Check your frontend - the messages should appear in the chat")
print("💡 The 'resolved' message should auto-resolve the incident")
