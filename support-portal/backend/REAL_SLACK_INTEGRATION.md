# Real Slack Integration Guide - Operations Team Communication

## 🔄 How Operations Team Communicates with Users

### Current Status
- ✅ **Mock/Simulated**: Frontend shows simulated messages from operations team
- ⚠️ **Not Connected**: Messages are not sent to/from real Slack workspace

### Production Setup Required

---

## 📋 Step-by-Step Implementation

### **1. Create Slack App (Slack Workspace)**

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "P1 Incident Manager"
4. Choose your workspace

### **2. Enable Required Slack Features**

#### **A. Incoming Webhooks (Backend → Slack)**
- Navigate to "Incoming Webhooks" → Enable
- Click "Add New Webhook to Workspace"
- Select channel: `#p1-incidents`
- Copy webhook URL → Add to `.env`

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### **B. Event Subscriptions (Slack → Backend)**
- Navigate to "Event Subscriptions" → Enable
- Request URL: `https://your-backend.com/api/slack/events`
- Subscribe to bot events:
  - `message.channels` - Monitor channel messages
  - `message.groups` - Monitor private channel messages

#### **C. OAuth & Permissions**
Add these Bot Token Scopes:
- `chat:write` - Send messages
- `channels:read` - Read channel info
- `channels:history` - Read message history
- `users:read` - Get user info
- `incoming-webhook` - Post messages

### **3. Backend Integration**

#### **Add to app.py**

```python
from slack_webhooks import SlackMessageHandler, SLACK_MESSAGES_SCHEMA

# Initialize
slack_handler = SlackMessageHandler(db_manager)

# Apply schema
with db_manager.get_connection() as conn:
    conn.executescript(SLACK_MESSAGES_SCHEMA)

# Endpoint 1: Receive messages FROM Slack (operations team responses)
@app.post("/api/slack/events")
async def handle_slack_event(request: Request):
    """
    Slack sends POST here when operations team replies in channel
    """
    body = await request.json()
    result = slack_handler.handle_slack_event(body)
    return result

# Endpoint 2: Fetch messages for frontend
@app.get("/api/incidents/{incident_id}/messages")
async def get_incident_messages(incident_id: str):
    """
    Frontend polls this to get latest messages from operations team
    """
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, user_name, message_text, 
                   direction, created_at
            FROM slack_messages
            WHERE incident_id = ?
            ORDER BY created_at ASC
        """, (incident_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "user": row[1],
                "message": row[2],
                "type": "user" if row[3] == "inbound" else "outbound",
                "timestamp": row[4]
            })
    
    return {"messages": messages}

# Endpoint 3: Send user message TO Slack
@app.post("/api/incidents/{incident_id}/messages")
async def send_user_message(incident_id: str, request: Request):
    """
    When user types message in frontend, send to Slack channel
    """
    body = await request.json()
    message_text = body.get("message")
    
    # Get incident details
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT slack_webhook_url, slack_channel_id
            FROM p1_incidents
            WHERE incident_id = ?
        """, (incident_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(404, "Incident not found")
        
        webhook_url = row[0]
    
    # Send to Slack
    import requests
    response = requests.post(webhook_url, json={
        "text": f"📩 *User Message:* {message_text}",
        "username": "User",
        "icon_emoji": ":user:"
    })
    
    if response.status_code != 200:
        raise HTTPException(500, "Failed to send message to Slack")
    
    # Store in database
    message_id = slack_handler._store_slack_message(
        incident_id=incident_id,
        ticket_id=body.get("ticket_id"),
        user_id="user",
        user_name="You",
        message=message_text,
        slack_ts=str(datetime.now().timestamp()),
        direction="outbound"
    )
    
    return {"status": "success", "message_id": message_id}
```

### **4. Frontend Integration**

#### **Update SlackIntegration.tsx**

```typescript
// Replace mock messages with real API calls

useEffect(() => {
  // Poll for new messages every 5 seconds
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`/api/incidents/${incidentId}/messages`);
      const data = await response.json();
      setMessages(data.messages);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  }, 5000);
  
  return () => clearInterval(interval);
}, [incidentId]);

// Send user message
const handleSendMessage = async () => {
  if (!newMessage.trim()) return;
  
  try {
    const response = await fetch(`/api/incidents/${incidentId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: newMessage,
        ticket_id: ticketId
      })
    });
    
    if (response.ok) {
      setNewMessage('');
      // Message will appear on next poll
    }
  } catch (error) {
    console.error('Failed to send message:', error);
  }
};
```

### **5. Deployment Checklist**

- [ ] Set up Slack app in workspace
- [ ] Get webhook URL and add to `.env`
- [ ] Deploy backend with `/api/slack/events` endpoint
- [ ] Update Slack Event Subscriptions URL
- [ ] Verify Slack challenge request
- [ ] Test sending message from frontend → Slack
- [ ] Test replying in Slack → appears in frontend
- [ ] Set up message polling (5-10 seconds)
- [ ] Add error handling for network failures
- [ ] Consider WebSocket for real-time updates (optional)

---

## 🎯 Communication Flow (Production)

```
USER SENDS MESSAGE:
1. User types in frontend → POST /api/incidents/{id}/messages
2. Backend receives message → Sends to Slack webhook
3. Message appears in Slack channel #p1-incidents
4. Operations team sees message in real Slack

OPERATIONS TEAM RESPONDS:
1. Ops team types reply in Slack channel
2. Slack sends webhook → POST /api/slack/events
3. Backend stores message in slack_messages table
4. Frontend polls → GET /api/incidents/{id}/messages
5. New message appears in user's chat interface
```

---

## 🔐 Security Considerations

1. **Verify Slack requests** - Check `X-Slack-Signature` header
2. **Rate limiting** - Prevent message spam
3. **Authentication** - Only authorized users can send messages
4. **Message sanitization** - Prevent XSS/injection
5. **Audit logging** - Track all communications

---

## 🚀 Alternative: WebSocket Real-time

For instant delivery (no polling), use WebSocket:

```python
# Backend WebSocket endpoint
@app.websocket("/ws/incidents/{incident_id}")
async def incident_websocket(websocket: WebSocket, incident_id: str):
    await websocket.accept()
    
    # When Slack message arrives, push to all connected clients
    while True:
        message = await websocket.receive_text()
        # Broadcast to all clients in this incident
        await manager.broadcast(incident_id, message)
```

---

## 📊 Monitoring & Metrics

Track these metrics:
- Message delivery success rate
- Average response time from ops team
- Number of active P1 incidents
- Slack API error rates
- User satisfaction with communication

---

## 🆘 Troubleshooting

**Messages not appearing in Slack?**
- Check webhook URL is correct
- Verify Slack app has `incoming-webhook` permission
- Check backend logs for API errors

**Ops team messages not showing in frontend?**
- Verify Event Subscriptions URL is reachable
- Check Slack is sending events (Event Logs in Slack app)
- Confirm `slack_messages` table exists
- Check frontend polling is working

**Duplicate messages?**
- Slack retries failed webhooks
- Use message ID deduplication
- Check for multiple bot instances
