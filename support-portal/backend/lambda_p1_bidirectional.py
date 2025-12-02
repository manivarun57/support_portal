#!/usr/bin/env python3
"""
P1 Incident Management Lambda with Bidirectional Slack Communication
- User creates P1 → Ops notified in Slack
- User comments → Ops sees in Slack thread
- Ops replies in Slack → User notified via email

Environment Variables Required:
- SLACK_BOT_TOKEN: Your Slack bot token
- SLACK_OPS_CHANNEL: Operations team channel ID (default: C0A10UFAT9N)
"""

import os
import json
import boto3
import requests
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

# -----------------------------
# CONFIGURATION
# -----------------------------
DYNAMO_REGION = os.environ.get("DYNAMO_REGION", "ap-south-1")
TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "pi-tickets-p1-slack-storage")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_API = "https://slack.com/api"

# Operations team channel
OPS_CHANNEL = os.environ.get("SLACK_OPS_CHANNEL", "C0A10UFAT9N")

# Get bot user ID to ignore its own messages (leave empty for now)
SLACK_BOT_USER_ID = os.environ.get("SLACK_BOT_USER_ID", "")

dynamodb = boto3.resource("dynamodb", region_name=DYNAMO_REGION)
table = dynamodb.Table(TABLE_NAME)


# -----------------------------
# Helper: Slack sender
# -----------------------------
def slack_post_message(channel, text, blocks=None, thread_ts=None):
    """Post message to Slack channel or thread"""
    try:
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "channel": channel,
            "text": text
        }

        if blocks:
            payload["blocks"] = blocks

        if thread_ts:
            payload["thread_ts"] = thread_ts

        r = requests.post(
            f"{SLACK_API}/chat.postMessage",
            headers=headers,
            json=payload,
            timeout=10
        )

        response_data = r.json()
        print(f"✅ Slack response: {response_data}")
        
        if not response_data.get("ok"):
            print(f"❌ Slack error: {response_data.get('error')}")
            return None
            
        return response_data

    except Exception as e:
        print(f"❌ Slack post error: {e}")
        return None


# -----------------------------
# Create a P1 incident
# -----------------------------
def create_p1_incident(data):
    """Create new P1 incident with Slack notification"""
    try:
        incident_id = f"P1-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.utcnow().isoformat()

        item = {
            "client_id": data["client_id"],
            "incident_id": incident_id,
            "client_name": data.get("client_name", "Unknown"),
            "user_id": data.get("user_id", ""),
            "user_name": data.get("user_name", "Unknown User"),
            "user_email": data.get("user_email", ""),
            "ticket_id": data.get("ticket_id", ""),
            "subject": data["subject"],
            "description": data["description"],
            "category": data.get("category", "General"),
            "priority": "P1",
            "status": "active",
            "slack_thread_ts": "",
            "slack_channel_id": OPS_CHANNEL,
            "slack_messages": [],
            "created_at": timestamp,
            "updated_at": timestamp,
            "resolved_at": None
        }

        table.put_item(Item=item)
        print(f"✅ P1 Incident created: {incident_id}")

        # Send initial Slack alert with formatted blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 NEW P1 CRITICAL INCIDENT",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Incident ID:*\n{incident_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Client:*\n{item['client_name']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Subject:*\n{item['subject']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{item['description']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n{item['user_name']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Email:*\n{item['user_email']}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Created: {timestamp} | Status: 🔴 Active"
                    }
                ]
            }
        ]

        slack_resp = slack_post_message(
            OPS_CHANNEL,
            f"🚨 P1 Critical: {item['subject']}",
            blocks=blocks
        )

        thread_ts = None
        if slack_resp and slack_resp.get("ok"):
            thread_ts = slack_resp.get("ts")
            
            # Update DynamoDB with thread_ts
            table.update_item(
                Key={"client_id": item["client_id"], "incident_id": incident_id},
                UpdateExpression="SET slack_thread_ts = :ts, updated_at = :updated",
                ExpressionAttributeValues={
                    ":ts": thread_ts,
                    ":updated": datetime.utcnow().isoformat()
                }
            )
            print(f"✅ Slack thread created: {thread_ts}")

        return {
            "success": True,
            "incident_id": incident_id,
            "thread_ts": thread_ts,
            "created_at": timestamp
        }

    except Exception as e:
        print(f"❌ Error creating P1 incident: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


# -----------------------------
# USER COMMENT → notify OPS
# -----------------------------
def add_user_comment(data):
    """User adds comment → notify ops team in Slack thread"""
    try:
        client_id = data["client_id"]
        incident_id = data["incident_id"]
        message = data["message"]
        user_name = data.get("user_name", "User")

        resp = table.get_item(Key={"client_id": client_id, "incident_id": incident_id})
        item = resp.get("Item")

        if not item:
            return {"success": False, "error": "Incident not found"}

        thread_ts = item.get("slack_thread_ts")
        
        if not thread_ts:
            print("⚠️ No Slack thread found for this incident")
            return {"success": False, "error": "No Slack thread available"}

        # Save comment to DB
        comment_entry = {
            "from": "user",
            "user_name": user_name,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        table.update_item(
            Key={"client_id": client_id, "incident_id": incident_id},
            UpdateExpression="SET slack_messages = list_append(if_not_exists(slack_messages, :empty), :new), updated_at = :updated",
            ExpressionAttributeValues={
                ":new": [comment_entry],
                ":empty": [],
                ":updated": datetime.utcnow().isoformat()
            }
        )

        # Notify OPS in Slack thread
        slack_post_message(
            OPS_CHANNEL,
            f"👤 *{user_name}* says:\n{message}",
            thread_ts=thread_ts
        )

        print(f"✅ User comment added to incident {incident_id}")
        return {"success": True, "message": "Comment added"}

    except Exception as e:
        print(f"❌ Error adding user comment: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# -----------------------------
# OPS COMMENT (Slack event) → notify USER
# -----------------------------
def handle_slack_event(event_data):
    """
    Slack event when ops team replies in thread
    
    Event format from Slack:
    {
       "type": "event_callback",
       "event": {
           "type": "message",
           "channel": "C0A10UFAT9N",
           "user": "U12345",
           "text": "We're investigating this issue",
           "thread_ts": "1234567890.123456",
           "ts": "1234567890.123457"
       }
    }
    """
    try:
        # Handle Slack URL verification challenge
        if event_data.get("type") == "url_verification":
            return {
                "statusCode": 200,
                "body": json.dumps({"challenge": event_data.get("challenge")})
            }

        # Get the actual event
        event = event_data.get("event", {})
        
        # Ignore non-message events
        if event.get("type") != "message":
            return {"success": True, "message": "Not a message event"}

        # Ignore bot's own messages
        if event.get("bot_id") or event.get("user") == SLACK_BOT_USER_ID:
            print("⏭️ Ignoring bot message")
            return {"success": True, "message": "Bot message ignored"}

        # Ignore messages without thread (not a reply)
        thread_ts = event.get("thread_ts")
        if not thread_ts:
            print("⏭️ Not a threaded message, ignoring")
            return {"success": True, "message": "Not a threaded message"}

        text = event.get("text", "")
        slack_user = event.get("user", "Unknown")

        print(f"📨 Ops reply in thread {thread_ts}: {text}")

        # Find incident by thread_ts
        resp = table.scan(
            FilterExpression=Attr("slack_thread_ts").eq(thread_ts)
        )
        items = resp.get("Items", [])
        
        if not items:
            print(f"⚠️ No incident found for thread_ts: {thread_ts}")
            return {"success": False, "error": "Incident not found for thread_ts"}

        incident = items[0]

        # Save OPS message to DynamoDB
        ops_comment = {
            "from": "ops",
            "slack_user": slack_user,
            "message": text,
            "timestamp": datetime.utcnow().isoformat()
        }

        table.update_item(
            Key={
                "client_id": incident["client_id"],
                "incident_id": incident["incident_id"]
            },
            UpdateExpression="SET slack_messages = list_append(if_not_exists(slack_messages, :empty), :new), updated_at = :updated",
            ExpressionAttributeValues={
                ":new": [ops_comment],
                ":empty": [],
                ":updated": datetime.utcnow().isoformat()
            }
        )

        # Notify user via email (console mode)
        email_content = f"""
{'='*70}
📧 EMAIL NOTIFICATION - OPS TEAM UPDATE
{'='*70}
To: {incident['user_email']}
Subject: Update on your P1 incident {incident['incident_id']}
{'─'*70}

Hi {incident['user_name']},

Our operations team has posted an update on your P1 critical incident:

*Subject:* {incident['subject']}
*Incident ID:* {incident['incident_id']}

*Operations Team Update:*
{text}

────────────────────
You can reply to this incident through the support portal.

Thank you,
Support Portal Operations Team
{'='*70}
"""
        print(email_content)

        print(f"✅ Ops comment saved and user notified")
        return {"success": True, "message": "User notified"}

    except Exception as e:
        print(f"❌ Error handling Slack event: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


# -----------------------------
# Get incident with messages
# -----------------------------
def get_incident_with_messages(data):
    """Get incident details including all messages"""
    try:
        client_id = data["client_id"]
        incident_id = data["incident_id"]

        resp = table.get_item(Key={"client_id": client_id, "incident_id": incident_id})
        item = resp.get("Item")

        if not item:
            return {"success": False, "error": "Incident not found"}

        return {
            "success": True,
            "incident": item
        }

    except Exception as e:
        print(f"❌ Error getting incident: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# -----------------------------
# LAMBDA ENTRY POINT
# -----------------------------
def lambda_handler(event, context):
    """
    AWS Lambda entry point with multiple actions
    
    Actions:
    - create_p1_incident: Create new P1 incident
    - user_comment: User adds comment
    - slack_event: Ops team replied in Slack
    - get_incident: Get incident with all messages
    """
    print(f"📥 Lambda invoked: {json.dumps(event)}")

    try:
        # Check if this is a Slack event (different format)
        if event.get("type") in ["url_verification", "event_callback"]:
            result = handle_slack_event(event)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result)
            }

        # Standard API Gateway format
        action = event.get("action")
        data = event.get("data", {})

        if action == "create_p1_incident":
            result = create_p1_incident(data)
        elif action == "user_comment":
            result = add_user_comment(data)
        elif action == "slack_event":
            result = handle_slack_event(data)
        elif action == "get_incident":
            result = get_incident_with_messages(data)
        else:
            result = {
                "success": False,
                "error": f"Unknown action: {action}",
                "supported_actions": [
                    "create_p1_incident",
                    "user_comment",
                    "slack_event",
                    "get_incident"
                ]
            }

        return {
            "statusCode": 200 if result.get("success") else 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result)
        }

    except Exception as e:
        print(f"❌ Lambda error: {e}")
        import traceback
        print(traceback.format_exc())
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }


# -----------------------------
# LOCAL TESTING
# -----------------------------
if __name__ == "__main__":
    # Test creating P1 incident
    test_event = {
        "action": "create_p1_incident",
        "data": {
            "client_id": "merchant_test123",
            "client_name": "TechCorp Inc.",
            "user_id": "user_test456",
            "user_name": "Dheeraj",
            "user_email": "dheeraj.narayanam@payintelli.com",
            "ticket_id": "TKT-001",
            "subject": "Critical Database Failure",
            "description": "Production database is not responding. Multiple users affected.",
            "category": "Infrastructure"
        }
    }
    
    print("=" * 70)
    print("LOCAL TEST - Create P1 Incident")
    print("=" * 70)
    
    result = lambda_handler(test_event, None)
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    print(json.dumps(json.loads(result["body"]), indent=2))
