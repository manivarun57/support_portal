"""
Enhanced Slack Integration with Channel History and Filtering

This module provides:
1. Post all P1 incidents to a dedicated Slack channel
2. Each incident becomes a thread
3. All messages appear as replies in that thread
4. Can view history of all incidents (resolved and active)
5. Filter by status and category
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class SlackChannelManager:
    """Manages P1 incidents in a Slack channel with full history and threading
    
    Now supports multi-client routing - each merchant/client gets their own Slack channel
    """
    
    def __init__(self, bot_token: str, channel_id: str = None, db_connection=None):
        """
        Initialize Slack Channel Manager
        
        Args:
            bot_token: Slack Bot User OAuth Token (starts with xoxb-)
            channel_id: Default Slack channel ID (optional if using merchant-specific channels)
            db_connection: Database connection for fetching merchant-specific channels
        """
        self.bot_token = bot_token
        self.channel_id = channel_id  # Default channel
        self.base_url = "https://slack.com/api"
        self.db_connection = db_connection
    
    def get_merchant_channel(self, merchant_id: str) -> str:
        """
        Get the Slack channel ID for a specific merchant
        
        Args:
            merchant_id: The merchant/client ID
            
        Returns:
            Slack channel ID for the merchant, or default channel_id if not found
        """
        if not self.db_connection or not merchant_id:
            return self.channel_id
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT slack_channel_id 
                FROM merchants 
                WHERE merchant_id = ?
            """, (merchant_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
        except Exception as e:
            print(f"⚠️ Error fetching merchant channel: {e}")
        
        return self.channel_id
        
    def post_incident(self, incident: Dict[str, Any]) -> Optional[str]:
        """
        Post a new P1 incident to the Slack channel as a parent message
        Routes to merchant-specific channel if merchant_id is provided
        
        Returns:
            thread_ts: The timestamp of the posted message (used for threading replies)
        """
        incident_id = incident.get('incident_id', 'UNKNOWN')
        ticket_id = incident.get('ticket_id', 'UNKNOWN')
        subject = incident.get('subject', 'No subject')
        description = incident.get('description', 'No description')
        merchant_name = incident.get('merchant_name', 'Unknown')
        merchant_id = incident.get('merchant_id', None)
        user_name = incident.get('user_name', 'Unknown')
        user_email = incident.get('user_email', '')
        category = incident.get('category', 'P1 Critical')
        created_at = incident.get('created_at', datetime.now().isoformat())
        
        # Get merchant-specific channel or use default
        target_channel = self.get_merchant_channel(merchant_id) if merchant_id else self.channel_id
        
        if not target_channel:
            print(f"❌ No Slack channel configured for merchant {merchant_id or 'default'}")
            return None
        
        print(f"🎯 Posting to channel: {target_channel} for merchant: {merchant_name}")
        
        # Create rich message block with Email-Subject format
        message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📧 Email-Subject: P1 critical has been made",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🚨 P1 Critical Title:*\n{subject}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📝 Description:*\n{description}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*👤 Username:*\n{user_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*🏢 Client/Merchant:*\n{merchant_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*📧 Email:*\n{user_email}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*🔴 Status:*\nActive"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 Created: {created_at} | 🎫 Incident ID: {incident_id} | Ticket: {ticket_id[:8]}"
                    }
                ]
            }
        ]
        
        # Post to Slack with @here notification for operations team
        response = requests.post(
            f"{self.base_url}/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            },
            json={
                "channel": target_channel,
                "blocks": message_blocks,
                "text": f"<!here> 📧 Email-Subject: P1 critical has been made - {subject}"  # Fallback text with @here notification
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                thread_ts = data.get("ts")
                print(f"✅ Posted incident {incident_id} to Slack channel {target_channel} (thread: {thread_ts})")
                return thread_ts
            else:
                print(f"❌ Slack API error: {data.get('error')}")
                return None
        else:
            print(f"❌ Failed to post to Slack: {response.status_code}")
            return None
    
    def post_reply(self, thread_ts: str, message: str, user_name: str = "User", 
                   is_resolution: bool = False, channel_id: str = None) -> bool:
        """
        Post a reply to an incident thread
        
        Args:
            thread_ts: The timestamp of the parent message (thread)
            message: The message text
            user_name: Name of the user posting
            is_resolution: True if this message resolves the incident
            channel_id: Specific channel ID (optional, uses default if not provided)
        """
        target_channel = channel_id or self.channel_id
        icon = "✅" if is_resolution else "💬"
        
        # Add @here mention for user messages to notify operations team
        # @here notifies all active members in the channel
        text_with_notification = f"<!here> {icon} *{user_name}:* {message}" if not is_resolution else f"{icon} *{user_name}:* {message}"
        
        response = requests.post(
            f"{self.base_url}/chat.postMessage",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            },
            json={
                "channel": target_channel,
                "thread_ts": thread_ts,  # This makes it a reply in the thread
                "text": text_with_notification
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print(f"✅ Posted reply to thread {thread_ts}")
                return True
            else:
                print(f"❌ Slack API error: {data.get('error')}")
                return False
        else:
            print(f"❌ Failed to post reply: {response.status_code}")
            return False
    
    def update_incident_status(self, thread_ts: str, incident_id: str, 
                               status: str = "resolved", channel_id: str = None) -> bool:
        """
        Update the original incident message to show it's resolved
        
        Args:
            thread_ts: Thread timestamp
            incident_id: Incident ID
            status: New status (resolved/active)
            channel_id: Specific channel ID (optional, uses default if not provided)
        """
        target_channel = channel_id or self.channel_id
        emoji = "✅" if status == "resolved" else "🔴"
        status_text = "Resolved" if status == "resolved" else "Active"
        
        # First, get the original message
        response = requests.post(
            f"{self.base_url}/conversations.history",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            },
            json={
                "channel": target_channel,
                "latest": thread_ts,
                "limit": 1,
                "inclusive": True
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch message: {response.status_code}")
            return False
        
        data = response.json()
        if not data.get("ok") or not data.get("messages"):
            print(f"❌ Could not find message")
            return False
        
        original_message = data["messages"][0]
        blocks = original_message.get("blocks", [])
        
        # Update the status field in the blocks
        for block in blocks:
            if block.get("type") == "section" and block.get("fields"):
                for field in block["fields"]:
                    if field.get("text", "").startswith("*Status:*"):
                        field["text"] = f"*Status:*\n{emoji} {status_text}"
        
        # Update the message
        update_response = requests.post(
            f"{self.base_url}/chat.update",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            },
            json={
                "channel": target_channel,
                "ts": thread_ts,
                "blocks": blocks
            }
        )
        
        if update_response.status_code == 200:
            update_data = update_response.json()
            if update_data.get("ok"):
                print(f"✅ Updated incident {incident_id} status to {status}")
                return True
        
        print(f"❌ Failed to update status")
        return False
    
    def get_channel_history(self, limit: int = 100, channel_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all messages from the channel (for viewing history)
        
        Args:
            limit: Maximum number of messages to retrieve
            channel_id: Specific channel ID (optional, uses default if not provided)
        """
        target_channel = channel_id or self.channel_id
        
        response = requests.post(
            f"{self.base_url}/conversations.history",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            },
            json={
                "channel": target_channel,
                "limit": limit
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data.get("messages", [])
        
        return []
    
    def get_thread_replies(self, thread_ts: str, channel_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all replies in a thread (for syncing messages from Slack to frontend)
        This is the KEY method for WhatsApp-like experience without ngrok!
        
        Args:
            thread_ts: Thread timestamp
            channel_id: Specific channel ID (optional, uses default if not provided)
        """
        target_channel = channel_id or self.channel_id
        
        response = requests.get(
            f"{self.base_url}/conversations.replies",
            headers={
                "Authorization": f"Bearer {self.bot_token}",
            },
            params={
                "channel": target_channel,
                "ts": thread_ts
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Slack API Response: {data}")  # DEBUG
            if data.get("ok"):
                messages = data.get("messages", [])
                print(f"📨 Found {len(messages)} total messages in thread")  # DEBUG
                # Skip the first message (it's the parent thread)
                return messages[1:] if len(messages) > 1 else []
            else:
                print(f"❌ Slack API error in get_thread_replies: {data.get('error')}")  # DEBUG
        else:
            print(f"❌ HTTP error in get_thread_replies: {response.status_code}")  # DEBUG
        
        return []


# Usage instructions
SETUP_INSTRUCTIONS = """
=============================================================================
SLACK BOT SETUP FOR INCIDENT HISTORY AND FILTERING
=============================================================================

To use this enhanced Slack integration, you need to:

1. CREATE A SLACK APP (if you don't have one):
   - Go to https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"
   - Name it "P1 Incident Manager"
   - Select your workspace

2. ADD BOT SCOPES (OAuth & Permissions):
   - chat:write - Post messages to channels
   - chat:write.public - Post to public channels without joining
   - channels:history - View messages in public channels
   - channels:read - View basic channel info

3. INSTALL APP TO WORKSPACE:
   - Click "Install to Workspace"
   - Authorize the app
   - Copy the "Bot User OAuth Token" (starts with xoxb-)

4. GET CHANNEL ID:
   - Open Slack
   - Right-click on your channel (e.g., #p1-incidents)
   - Click "View channel details"
   - Scroll down to find the Channel ID (e.g., C1234567890)

5. UPDATE YOUR BACKEND:
   Replace in app.py:
   
   BOT_TOKEN = "xoxb-YOUR-BOT-TOKEN-HERE"
   CHANNEL_ID = "C1234567890"  # Your channel ID
   
   slack_channel_manager = SlackChannelManager(BOT_TOKEN, CHANNEL_ID)

6. BENEFITS:
   ✅ All P1 incidents appear as individual threads in one channel
   ✅ Full conversation history for each incident
   ✅ Can scroll back to see resolved incidents
   ✅ Each incident thread contains all messages
   ✅ Status updates visible in the main message
   ✅ Filter by looking at thread titles and status emojis

=============================================================================
"""

if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)
