# Slack Webhook Handlers for Real-time Communication
# This file handles incoming messages FROM Slack (operations team responses)

from typing import Dict, Any
import json
from datetime import datetime

class SlackMessageHandler:
    """
    Handles incoming Slack messages from operations team.
    When ops team replies in Slack, Slack sends webhook to this handler.
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        
    def handle_slack_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming Slack event (message from operations team)
        
        Slack Event Format:
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "user": "U0A10UF1U4Q",
                "text": "We're investigating the database connection issue",
                "channel": "C07V57P5N31",
                "ts": "1701388800.123456"
            }
        }
        """
        
        if event_data.get("type") == "url_verification":
            # Slack verification challenge
            return {"challenge": event_data.get("challenge")}
        
        event = event_data.get("event", {})
        
        if event.get("type") != "message":
            return {"status": "ignored", "reason": "not a message event"}
        
        # Ignore bot messages to prevent loops
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return {"status": "ignored", "reason": "bot message"}
        
        # Extract message details
        channel_id = event.get("channel")
        user_id = event.get("user")
        text = event.get("text")
        timestamp = event.get("ts")
        
        # Find the incident associated with this Slack channel
        incident = self._get_incident_by_channel(channel_id)
        
        if not incident:
            return {"status": "error", "reason": "incident not found for channel"}
        
        # Get user info from Slack API (optional - for display names)
        user_name = self._get_slack_user_name(user_id)
        
        # Store message in database
        message_id = self._store_slack_message(
            incident_id=incident["incident_id"],
            ticket_id=incident["ticket_id"],
            user_id=user_id,
            user_name=user_name,
            message=text,
            slack_ts=timestamp,
            direction="inbound"  # from Slack to user
        )
        
        return {
            "status": "success",
            "message_id": message_id,
            "incident_id": incident["incident_id"]
        }
    
    def _get_incident_by_channel(self, channel_id: str) -> Dict[str, Any]:
        """Look up P1 incident by Slack channel ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT incident_id, ticket_id, created_at
                FROM p1_incidents
                WHERE slack_channel_id = ?
                AND status = 'active'
            """, (channel_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "incident_id": row[0],
                    "ticket_id": row[1],
                    "created_at": row[2]
                }
        return None
    
    def _get_slack_user_name(self, user_id: str) -> str:
        """
        Get human-readable name from Slack user ID.
        In production, call Slack API: users.info
        """
        # For now, return a mapping or fallback
        user_map = {
            "U0A10UF1U4Q": "Sarah Chen",
            "U0B11VG2V5R": "Mike Rodriguez",
            "U0C12WH3W6S": "David Kim"
        }
        return user_map.get(user_id, f"Ops Team Member ({user_id})")
    
    def _store_slack_message(
        self,
        incident_id: str,
        ticket_id: str,
        user_id: str,
        user_name: str,
        message: str,
        slack_ts: str,
        direction: str
    ) -> str:
        """Store Slack message in database for display in frontend"""
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            message_id = f"msg-{datetime.now().strftime('%Y%m%d%H%M%S')}-{slack_ts.replace('.', '')}"
            
            cursor.execute("""
                INSERT INTO slack_messages 
                (message_id, incident_id, ticket_id, slack_user_id, user_name, 
                 message_text, slack_timestamp, direction, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                incident_id,
                ticket_id,
                user_id,
                user_name,
                message,
                slack_ts,
                direction,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            
        return message_id


# Database Schema for Slack Messages
SLACK_MESSAGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS slack_messages (
    message_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    ticket_id TEXT NOT NULL,
    slack_user_id TEXT,
    user_name TEXT NOT NULL,
    message_text TEXT NOT NULL,
    slack_timestamp TEXT,
    direction TEXT NOT NULL,  -- 'inbound' (from Slack) or 'outbound' (to Slack)
    created_at TEXT NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES p1_incidents(incident_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);

CREATE INDEX IF NOT EXISTS idx_slack_messages_incident 
ON slack_messages(incident_id);

CREATE INDEX IF NOT EXISTS idx_slack_messages_ticket 
ON slack_messages(ticket_id);
"""
