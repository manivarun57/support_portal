# P1 Critical Incident Workflow Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [User Journey](#user-journey)
4. [Technical Flow](#technical-flow)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Slack Integration](#slack-integration)
8. [Resolution Workflow](#resolution-workflow)
9. [Security & Access Control](#security--access-control)

---

## Overview

### Purpose
The P1 Critical Incident system provides an **urgent escalation path** for critical production issues requiring immediate attention from operations teams. It combines ticket tracking, real-time Slack communication, and resolution workflows.

### Key Features
- ⚡ **Immediate Slack Notifications** - Operations team alerted within seconds
- 💬 **Embedded Real-Time Chat** - Direct communication without leaving the application
- 🔒 **User-Specific Access** - Users only see their own P1 incidents
- 📊 **Dual Database Storage** - PostgreSQL for tickets, specialized P1 tracking
- ✅ **Resolution Workflow** - Structured incident closure with RCA documentation
- 🔄 **Two-Way Slack Integration** - Messages flow between user and operations team

### When to Use P1 Critical
- 🚨 Complete system outages
- 💳 Payment processing failures
- 🔐 Security breaches or vulnerabilities
- 📉 Critical data loss or corruption
- ⏱️ Performance degradation affecting all users
- 🔥 Any issue causing significant business impact

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│  Next.js Frontend (Port 3000)                                   │
│  - Form: /p1-critical                                           │
│  - Success Page: /p1-critical/success/[id]                     │
│  - Ticket List: /tickets (filtered by user)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API LAYER                           │
│  Python FastAPI (Port 8000)                                     │
│  - POST /api/p1-incident/create                                 │
│  - GET /api/p1-incidents (user-filtered)                        │
│  - POST /api/incidents/{id}/send-message                        │
│  - GET /api/incidents/{id}/messages                             │
│  - POST /api/incidents/{id}/resolve                             │
└─────────────────────────────────────────────────────────────────┘
           ↓                           ↓                    ↓
┌──────────────────┐      ┌──────────────────┐   ┌────────────────┐
│   PostgreSQL     │      │  Slack Webhook   │   │  Message DB    │
│   - tickets      │      │  (Real-time)     │   │  - slack_msgs  │
│   - p1_incidents │      │  Notifications   │   │  - history     │
└──────────────────┘      └──────────────────┘   └────────────────┘
```

### Technology Stack
- **Frontend**: Next.js 16, TypeScript, React, TailwindCSS
- **Backend**: Python 3.x, FastAPI, Chalice (AWS Lambda ready)
- **Databases**: PostgreSQL (primary), SQLite (local dev)
- **Integration**: Slack Webhooks, REST APIs
- **Deployment**: AWS Lambda + RDS (production), Local (development)

---

## User Journey

### Step 1: Access P1 Critical Form
```
User Action: Click "P1 Critical" in navigation
URL: http://localhost:3000/p1-critical
Page Components:
  - Priority badge (red, pulsing)
  - Warning messages about appropriate use
  - Incident creation form
```

### Step 2: Fill Incident Details
```
Required Fields:
  ✓ Title (max 200 chars)
  ✓ Description (detailed issue explanation)
  ✓ Impact Level: 
      - Critical (complete outage)
      - High (major functionality broken)
      - Medium (significant degradation)
  ✓ Category:
      - System Outage
      - Security Issue
      - Data Loss
      - Performance Issue
      - Payment Failure
      - Other Critical

Optional Fields:
  ○ Affected Systems
  ○ Steps to Reproduce
  ○ Screenshots/Logs
```

### Step 3: Submit & Immediate Response
```
Frontend Action:
  1. Validates form fields
  2. POST /api/p1-incident/create
  3. Shows loading state

Backend Processing (< 2 seconds):
  1. Creates ticket in tickets table
  2. Creates P1 incident record
  3. Sends Slack notification to operations team
  4. Generates unique incident ID (P1-YYYYMMDD-XXXXXXXX)
  5. Returns success with incident details

Frontend Response:
  1. Redirects to /p1-critical/success/[incident_id]
  2. Shows confirmation message
  3. Displays embedded Slack communication channel
```

### Step 4: Real-Time Communication
```
User Interface:
  - Embedded Slack chat window (900px height)
  - Message history (initial 10 welcome/info messages)
  - Input field for typing messages
  - Send button (Ctrl+Enter shortcut)
  - Connection status indicator

User Actions:
  ✓ Send messages to operations team
  ✓ Ask follow-up questions
  ✓ Request escalation
  ✓ Report related issues
  ✓ View message history

Operations Team (in Slack):
  ✓ Receives instant notifications
  ✓ Sees all user messages in dedicated channel
  ✓ Can reply directly in Slack
  ✓ Access to incident context and details
```

### Step 5: Incident Resolution
```
Resolution Triggers:
  - Operations team identifies root cause
  - Fix has been deployed and verified
  - User confirms issue is resolved
  - RCA (Root Cause Analysis) completed

Frontend Action:
  1. User clicks "Mark as Resolved" button
  2. Modal opens requesting:
     - Resolution summary
     - Root cause explanation
     - Preventive measures
     - Time to resolution
  3. Submits resolution data

Backend Processing:
  1. POST /api/incidents/{id}/resolve
  2. Updates ticket status to "Resolved"
  3. Updates P1 incident record
  4. Stores resolution details
  5. Sends closure notification to Slack
  6. Archives communication thread

Post-Resolution:
  - User can view resolved ticket in /tickets
  - Resolution details stored for future reference
  - Metrics updated (MTTR, resolution rate)
  - Incident tagged for post-mortem review
```

---

## Technical Flow

### Flow 1: P1 Incident Creation

```python
# 1. Frontend Form Submission
POST http://localhost:8000/api/p1-incident/create
Content-Type: application/json

{
  "title": "Payment Gateway Down",
  "description": "All payment transactions failing with 500 error",
  "priority": "P1",
  "category": "Payment Failure",
  "impact": "Critical",
  "user_email": "user@example.com",
  "user_name": "John Doe"
}

# 2. Backend Processing (app.py)
async def create_p1_incident(request: P1IncidentRequest):
    # Step 2a: Create base ticket
    ticket_id = str(uuid.uuid4())[:8]
    ticket = {
        "id": ticket_id,
        "title": request.title,
        "description": request.description,
        "priority": "P1",
        "status": "Open",
        "user_email": request.user_email,
        "created_at": datetime.utcnow()
    }
    db.insert("tickets", ticket)
    
    # Step 2b: Create P1 incident record
    incident_id = f"P1-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    p1_incident = {
        "incident_id": incident_id,
        "ticket_id": ticket_id,
        "severity": request.impact,
        "reported_by": request.user_name,
        "status": "ACTIVE",
        "slack_thread_ts": None,
        "created_at": datetime.utcnow()
    }
    db.insert("p1_incidents", p1_incident)
    
    # Step 2c: Send Slack notification
    slack_notifier = SlackNotifier(webhook_url)
    slack_message = {
        "text": f"🚨 P1 CRITICAL INCIDENT ALERT",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🚨 P1 CRITICAL INCIDENT ALERT*\n\n"
                           f"*Incident ID:* {incident_id}\n"
                           f"*Ticket ID:* {ticket_id}\n"
                           f"*Priority:* P1\n"
                           f"*Category:* {request.category}\n"
                           f"*Description:* {request.description}\n\n"
                           f"*Reported:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                           f"*Status:* 🔴 ACTIVE - IMMEDIATE RESPONSE REQUIRED"
                }
            }
        ]
    }
    response = slack_notifier.send_notification(slack_message)
    
    # Step 2d: Return success response
    return {
        "status": "success",
        "incident_id": incident_id,
        "ticket_id": ticket_id,
        "message": "P1 incident created and operations team notified"
    }

# 3. Frontend Redirect
window.location.href = `/p1-critical/success/${incident_id}`
```

### Flow 2: User Message → Slack

```typescript
// 1. User types message and clicks Send
const handleSendMessage = async () => {
    const response = await fetch(
        `http://localhost:8000/api/incidents/${incidentId}/send-message`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: messageText,
                user_name: 'User'
            })
        }
    );
    
    if (response.ok) {
        const data = await response.json();
        // Show confirmation
        addMessage({
            id: data.message_id,
            user: 'System',
            message: '✅ Message delivered to operations team via Slack',
            timestamp: new Date().toISOString()
        });
    }
};
```

```python
# 2. Backend receives and forwards to Slack
@app.post("/api/incidents/{incident_id}/send-message")
async def send_message_to_slack(incident_id: str, request: MessageRequest):
    # Step 2a: Validate incident exists
    incident = db.query("SELECT * FROM p1_incidents WHERE incident_id = ?", incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    
    # Step 2b: Store message in database
    message_id = f"msg-{int(time.time())}-{uuid.uuid4().hex[:9]}"
    db.insert("slack_messages", {
        "message_id": message_id,
        "incident_id": incident_id,
        "ticket_id": incident['ticket_id'],
        "user_name": request.user_name,
        "message_text": request.message,
        "direction": "outbound",
        "created_at": datetime.utcnow()
    })
    
    # Step 2c: Send to Slack webhook
    slack_payload = {
        "text": f"💬 *Message from {request.user_name}:*\n{request.message}",
        "thread_ts": incident['slack_thread_ts']  # Reply in thread
    }
    slack_response = requests.post(webhook_url, json=slack_payload)
    
    # Step 2d: Return confirmation
    return {
        "status": "success",
        "message_id": message_id,
        "sent_to_slack": slack_response.status_code == 200
    }
```

### Flow 3: Retrieve Message History

```python
# Backend endpoint
@app.get("/api/incidents/{incident_id}/messages")
async def get_incident_messages(incident_id: str, user_email: str):
    # Verify user owns this incident
    incident = db.query("""
        SELECT p.*, t.user_email 
        FROM p1_incidents p
        JOIN tickets t ON p.ticket_id = t.id
        WHERE p.incident_id = ? AND t.user_email = ?
    """, incident_id, user_email)
    
    if not incident:
        raise HTTPException(403, "Access denied")
    
    # Fetch all messages
    messages = db.query("""
        SELECT message_id, user_name, message_text, direction, created_at
        FROM slack_messages
        WHERE incident_id = ?
        ORDER BY created_at ASC
    """, incident_id)
    
    return {
        "messages": [
            {
                "id": msg['message_id'],
                "user": msg['user_name'],
                "message": msg['message_text'],
                "type": msg['direction'],
                "timestamp": msg['created_at']
            }
            for msg in messages
        ]
    }
```

### Flow 4: Incident Resolution

```python
# Frontend resolution submission
const handleResolve = async () => {
    const response = await fetch(
        `http://localhost:8000/api/incidents/${incidentId}/resolve`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                resolution_summary: resolutionText,
                root_cause: rootCauseText,
                preventive_measures: preventiveMeasures,
                resolved_by: currentUser
            })
        }
    );
};
```

```python
# Backend resolution processing
@app.post("/api/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, request: ResolutionRequest):
    # Update ticket status
    db.update("tickets", 
        {"status": "Resolved", "resolved_at": datetime.utcnow()},
        {"id": ticket_id}
    )
    
    # Update P1 incident
    db.update("p1_incidents",
        {
            "status": "RESOLVED",
            "resolution_summary": request.resolution_summary,
            "root_cause": request.root_cause,
            "resolved_at": datetime.utcnow(),
            "resolved_by": request.resolved_by
        },
        {"incident_id": incident_id}
    )
    
    # Notify Slack
    slack_notifier.send_notification({
        "text": f"✅ P1 Incident {incident_id} has been RESOLVED",
        "blocks": [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Resolution Summary:*\n{request.resolution_summary}\n\n"
                       f"*Root Cause:*\n{request.root_cause}"
            }
        }]
    })
    
    return {"status": "success", "message": "Incident resolved"}
```

---

## Database Schema

### Table: `tickets`
```sql
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,                    -- UUID (8 chars)
    title TEXT NOT NULL,                    -- Ticket title
    description TEXT NOT NULL,              -- Issue description
    priority TEXT NOT NULL,                 -- "P1", "P2", "P3", "P4"
    status TEXT NOT NULL,                   -- "Open", "In Progress", "Resolved", "Closed"
    category TEXT NOT NULL,                 -- Issue category
    user_email TEXT NOT NULL,               -- Reporter email (for filtering)
    user_name TEXT NOT NULL,                -- Reporter name
    assigned_to TEXT,                       -- Assigned team member
    created_at TEXT NOT NULL,               -- ISO 8601 timestamp
    updated_at TEXT,                        -- Last update timestamp
    resolved_at TEXT,                       -- Resolution timestamp
    resolution_notes TEXT                   -- Resolution details
);

-- Indexes for performance
CREATE INDEX idx_tickets_user_email ON tickets(user_email);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
```

### Table: `p1_incidents`
```sql
CREATE TABLE p1_incidents (
    incident_id TEXT PRIMARY KEY,           -- P1-YYYYMMDD-XXXXXXXX
    ticket_id TEXT NOT NULL,                -- Foreign key to tickets.id
    severity TEXT NOT NULL,                 -- "Critical", "High", "Medium"
    reported_by TEXT NOT NULL,              -- User name
    status TEXT NOT NULL,                   -- "ACTIVE", "INVESTIGATING", "RESOLVED"
    slack_thread_ts TEXT,                   -- Slack thread timestamp (for replies)
    created_at TEXT NOT NULL,               -- Incident creation time
    acknowledged_at TEXT,                   -- When ops team acknowledged
    resolved_at TEXT,                       -- Resolution time
    resolution_summary TEXT,                -- How it was fixed
    root_cause TEXT,                        -- Why it happened
    preventive_measures TEXT,               -- Future prevention
    resolved_by TEXT,                       -- Who resolved it
    mttr_minutes INTEGER,                   -- Mean Time To Resolution
    
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);

-- Indexes
CREATE INDEX idx_p1_incidents_ticket_id ON p1_incidents(ticket_id);
CREATE INDEX idx_p1_incidents_status ON p1_incidents(status);
CREATE INDEX idx_p1_incidents_created_at ON p1_incidents(created_at);
```

### Table: `slack_messages`
```sql
CREATE TABLE slack_messages (
    message_id TEXT PRIMARY KEY,            -- msg-timestamp-random
    incident_id TEXT NOT NULL,              -- Foreign key to p1_incidents
    ticket_id TEXT NOT NULL,                -- Foreign key to tickets
    user_name TEXT NOT NULL,                -- Sender name
    message_text TEXT NOT NULL,             -- Message content
    direction TEXT NOT NULL,                -- "outbound" (user→slack) or "inbound" (slack→user)
    created_at TEXT NOT NULL,               -- Message timestamp
    slack_ts TEXT,                          -- Slack message timestamp (for threading)
    
    FOREIGN KEY (incident_id) REFERENCES p1_incidents(incident_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);

-- Indexes
CREATE INDEX idx_slack_messages_incident_id ON slack_messages(incident_id);
CREATE INDEX idx_slack_messages_created_at ON slack_messages(created_at);
```

---

## API Endpoints

### 1. Create P1 Incident
```http
POST /api/p1-incident/create
Content-Type: application/json

Request:
{
  "title": "Database Connection Pool Exhausted",
  "description": "All API requests timing out. Database connections maxed out at 100.",
  "priority": "P1",
  "category": "System Outage",
  "impact": "Critical",
  "user_email": "john.doe@company.com",
  "user_name": "John Doe",
  "affected_systems": "API Server, Database",
  "steps_to_reproduce": "1. Send API request\n2. Observe timeout after 30s"
}

Response (200 OK):
{
  "status": "success",
  "incident_id": "P1-20251201-A3B4C5D6",
  "ticket_id": "e8ba22f9",
  "message": "P1 incident created and operations team notified",
  "slack_notification_sent": true,
  "created_at": "2025-12-01T14:23:45Z"
}

Error Responses:
400 - Invalid request data
500 - Server error during creation
503 - Slack notification failed (incident still created)
```

### 2. Get User's P1 Incidents
```http
GET /api/p1-incidents?user_email=john.doe@company.com
Authorization: Bearer <token>

Response (200 OK):
{
  "incidents": [
    {
      "incident_id": "P1-20251201-A3B4C5D6",
      "ticket_id": "e8ba22f9",
      "title": "Database Connection Pool Exhausted",
      "status": "ACTIVE",
      "severity": "Critical",
      "created_at": "2025-12-01T14:23:45Z",
      "time_elapsed": "45 minutes"
    }
  ],
  "total_count": 1,
  "active_count": 1
}
```

### 3. Send Message to Slack
```http
POST /api/incidents/{incident_id}/send-message
Content-Type: application/json

Request:
{
  "message": "We've restarted the database but connections still failing",
  "user_name": "John Doe"
}

Response (200 OK):
{
  "status": "success",
  "message_id": "msg-1733065425-abc123def",
  "sent_to_slack": true,
  "timestamp": "2025-12-01T14:30:25Z"
}

Error Responses:
404 - Incident not found
403 - User doesn't own this incident
500 - Failed to send to Slack
```

### 4. Get Message History
```http
GET /api/incidents/{incident_id}/messages?user_email=john.doe@company.com

Response (200 OK):
{
  "messages": [
    {
      "id": "msg-1733065000-xyz789",
      "user": "User",
      "message": "Database connections failing",
      "type": "outbound",
      "timestamp": "2025-12-01T14:23:20Z"
    },
    {
      "id": "msg-1733065100-ops456",
      "user": "Operations Team",
      "message": "Acknowledged. Checking database server status now.",
      "type": "inbound",
      "timestamp": "2025-12-01T14:25:00Z"
    }
  ],
  "total_messages": 2
}
```

### 5. Resolve Incident
```http
POST /api/incidents/{incident_id}/resolve
Content-Type: application/json

Request:
{
  "resolution_summary": "Increased database connection pool from 100 to 300",
  "root_cause": "Traffic spike caused connection pool exhaustion",
  "preventive_measures": "Added auto-scaling for connection pool, implemented connection monitoring",
  "resolved_by": "Operations Team"
}

Response (200 OK):
{
  "status": "success",
  "incident_id": "P1-20251201-A3B4C5D6",
  "resolved_at": "2025-12-01T15:10:00Z",
  "mttr_minutes": 47,
  "message": "Incident resolved successfully"
}
```

---

## Slack Integration

### Webhook Configuration
```python
# Environment variable
SLACK_WEBHOOK_URL=<your-slack-webhook-url-here>

# Backend configuration (app.py)
class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_notification(self, payload: dict) -> bool:
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False
```

### Message Formats

**P1 Incident Alert:**
```json
{
  "text": "🚨 P1 CRITICAL INCIDENT ALERT",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*🚨 P1 CRITICAL INCIDENT ALERT*\n\n*Incident ID:* P1-20251201-A3B4C5D6\n*Ticket ID:* e8ba22f9\n*Priority:* P1\n*Category:* System Outage\n*Description:* Database connections failing\n\n*Reported:* 2025-12-01 14:23:45 UTC\n*Status:* 🔴 ACTIVE - IMMEDIATE RESPONSE REQUIRED"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "Acknowledge"},
          "style": "primary",
          "action_id": "acknowledge_incident"
        },
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "View Details"},
          "url": "http://localhost:3000/tickets/e8ba22f9"
        }
      ]
    }
  ]
}
```

**User Message:**
```json
{
  "text": "💬 Message from User: We've restarted the database but connections still failing",
  "thread_ts": "1733065425.123456"  // Reply in thread
}
```

**Resolution Notification:**
```json
{
  "text": "✅ P1 Incident P1-20251201-A3B4C5D6 has been RESOLVED",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*✅ INCIDENT RESOLVED*\n\n*Incident ID:* P1-20251201-A3B4C5D6\n*Resolution Time:* 47 minutes\n\n*Resolution Summary:*\nIncreased database connection pool from 100 to 300\n\n*Root Cause:*\nTraffic spike caused connection pool exhaustion"
      }
    }
  ]
}
```

### Slack App Setup (For Inbound Messages)
```markdown
1. Create Slack App: https://api.slack.com/apps
2. Enable Incoming Webhooks (for outbound - ✅ done)
3. Enable Event Subscriptions (for inbound - TODO):
   - Request URL: https://your-backend.com/api/slack/events
   - Subscribe to: message.channels, message.groups
4. Install to workspace
5. Invite bot to P1 incident channel
```

---

## Resolution Workflow

### Resolution States
```
ACTIVE → INVESTIGATING → RESOLVED
  ↓           ↓              ↓
Open      In Progress    Closed
```

### Resolution Checklist
```markdown
Before marking P1 as resolved:
☐ Root cause identified and documented
☐ Fix deployed to production
☐ User confirmed issue is resolved
☐ Post-mortem scheduled (if needed)
☐ Preventive measures documented
☐ Knowledge base article created
☐ Metrics captured (MTTR, impact)
```

### Resolution Data Collection
```typescript
interface ResolutionData {
  resolution_summary: string;        // What was done to fix
  root_cause: string;                // Why it happened
  preventive_measures: string;       // How to prevent recurrence
  resolved_by: string;               // Team/person who resolved
  mttr_minutes: number;              // Time to resolution
  affected_users: number;            // Impact scope
  business_impact: string;           // Financial/operational impact
}
```

### Post-Resolution Actions
1. **Automatic:**
   - Status updated in database
   - Slack notification sent
   - MTTR calculated and stored
   - Ticket closed in system

2. **Manual (Operations Team):**
   - Post-mortem meeting (if needed)
   - Update runbooks
   - Create monitoring alerts
   - Review preventive measures
   - Update documentation

---

## Security & Access Control

### User Isolation
```python
# Users can ONLY see their own P1 incidents
@app.get("/api/p1-incidents")
async def get_user_incidents(user_email: str):
    incidents = db.query("""
        SELECT p.*, t.title, t.description
        FROM p1_incidents p
        JOIN tickets t ON p.ticket_id = t.id
        WHERE t.user_email = ?
        ORDER BY p.created_at DESC
    """, user_email)
    return {"incidents": incidents}
```

### Authorization Checks
```python
# Verify user owns incident before allowing actions
def verify_incident_access(incident_id: str, user_email: str) -> bool:
    incident = db.query("""
        SELECT 1 FROM p1_incidents p
        JOIN tickets t ON p.ticket_id = t.id
        WHERE p.incident_id = ? AND t.user_email = ?
    """, incident_id, user_email)
    return incident is not None
```

### Rate Limiting
```typescript
// Prevent message spam
const RATE_LIMIT = {
  maxMessages: 10,
  windowSeconds: 60
};

// Track message count
const messageCount = useRef(0);
const windowStart = useRef(Date.now());

const checkRateLimit = () => {
  const now = Date.now();
  if (now - windowStart.current > RATE_LIMIT.windowSeconds * 1000) {
    // Reset window
    messageCount.current = 0;
    windowStart.current = now;
  }
  
  if (messageCount.current >= RATE_LIMIT.maxMessages) {
    return false; // Rate limit exceeded
  }
  
  messageCount.current++;
  return true;
};
```

### Data Protection
- **Webhook URL**: Stored in environment variables, never exposed to frontend
- **User Data**: Email-based filtering, no cross-user data leakage
- **Message History**: Only accessible by incident owner
- **Database**: Parameterized queries prevent SQL injection

---

## Metrics & Monitoring

### Key Performance Indicators
```sql
-- Average resolution time
SELECT AVG(mttr_minutes) as avg_mttr
FROM p1_incidents
WHERE status = 'RESOLVED'
AND created_at > datetime('now', '-30 days');

-- P1 incidents by day
SELECT DATE(created_at) as date, COUNT(*) as count
FROM p1_incidents
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;

-- Resolution rate
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved,
  (SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as resolution_rate
FROM p1_incidents;
```

### Alerting Thresholds
- ⚠️ **MTTR > 60 minutes**: Review incident handling
- ⚠️ **Active incidents > 5**: Capacity issue
- ⚠️ **Resolution rate < 95%**: Process improvement needed
- ⚠️ **Slack notification failures**: Check webhook

---

## Troubleshooting Guide

### Issue: Slack notifications not sending
```bash
# Check webhook URL
echo $SLACK_WEBHOOK_URL

# Test webhook manually
curl -X POST https://hooks.slack.com/services/... \
  -H "Content-Type: application/json" \
  -d '{"text":"Test message"}'

# Check backend logs
tail -f logs/app.log | grep "Slack"
```

### Issue: Messages not appearing in chat
```bash
# Verify message stored in database
sqlite3 support_portal.db "SELECT * FROM slack_messages WHERE incident_id='P1-...';"

# Check API endpoint
curl http://localhost:8000/api/incidents/P1-.../messages?user_email=...

# Check browser console for errors
# Open DevTools → Console → Look for fetch errors
```

### Issue: User can't see their P1 incidents
```bash
# Verify user email matches
sqlite3 support_portal.db "SELECT * FROM tickets WHERE user_email='...';"

# Check p1_incidents table
sqlite3 support_portal.db "SELECT * FROM p1_incidents WHERE ticket_id IN (SELECT id FROM tickets WHERE user_email='...');"
```

---

## Best Practices

### For Users
1. ✅ Provide detailed descriptions with error messages
2. ✅ Include steps to reproduce
3. ✅ Attach relevant screenshots/logs
4. ✅ Respond promptly to operations team questions
5. ❌ Don't create duplicate P1s for same issue
6. ❌ Don't use P1 for non-critical issues

### For Operations Team
1. ✅ Acknowledge P1s within 2 minutes
2. ✅ Provide regular status updates
3. ✅ Document all troubleshooting steps
4. ✅ Complete thorough RCA
5. ✅ Update runbooks after resolution
6. ❌ Don't close without user confirmation

### For Developers
1. ✅ Monitor Slack webhook success rate
2. ✅ Log all P1 operations for audit
3. ✅ Implement retry logic for Slack sends
4. ✅ Keep database indexes optimized
5. ✅ Regular backups of incident data
6. ❌ Don't expose webhook URLs in frontend

---

## Future Enhancements

### Planned Features
- 🔄 Real-time message updates (WebSocket/SSE)
- 📊 P1 incident dashboard with charts
- 🔔 Browser push notifications
- 📱 Mobile app integration
- 🤖 AI-powered incident categorization
- 📈 Predictive analytics for incidents
- 🔗 Integration with monitoring tools (DataDog, New Relic)
- 📧 Email notifications backup
- 🎯 Automatic assignment based on category
- 📋 Incident templates for common issues

### Technical Debt
- [ ] Migrate from SQLite to PostgreSQL in production
- [ ] Implement proper authentication (OAuth2/JWT)
- [ ] Add request validation middleware
- [ ] Implement comprehensive error handling
- [ ] Add unit and integration tests
- [ ] Set up CI/CD pipeline
- [ ] Implement database migrations
- [ ] Add API documentation (Swagger/OpenAPI)

---

## Support Contacts

### Technical Issues
- **Backend API**: DevOps Team (devops@company.com)
- **Frontend UI**: Frontend Team (frontend@company.com)
- **Database**: Database Team (dba@company.com)
- **Slack Integration**: IT Support (itsupport@company.com)

### Business Questions
- **Process**: Support Manager (support@company.com)
- **Training**: Training Team (training@company.com)

---

**Document Version**: 1.0  
**Last Updated**: December 1, 2025  
**Maintained By**: Engineering Team
