# WhatsApp-Like Slack Integration Setup

## ✅ What's Been Integrated

Your support portal now has WhatsApp-like Slack integration:

1. **Threaded Conversations** - Each P1 incident creates a thread in Slack
2. **Persistent History** - All messages stay in the thread forever
3. **Resume Conversations** - Open old tickets and continue chatting
4. **Status Updates** - Incident status visible in main message (🔴 Active / ✅ Resolved)
5. **Full Context** - Merchant name, user details, category all visible

## 🔧 Setup Steps

### Step 1: Create Slack Bot

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "P1 Incident Manager"
4. Select your workspace → "Create App"

### Step 2: Add Bot Permissions

1. Go to "OAuth & Permissions" in left sidebar
2. Scroll to "Scopes" → "Bot Token Scopes"
3. Click "Add an OAuth Scope" and add these:
   - `chat:write` - Post messages
   - `chat:write.public` - Post to public channels
   - `channels:history` - View message history
   - `channels:read` - View channel info

### Step 3: Install App to Workspace

1. Scroll up to "OAuth Tokens"
2. Click "Install to Workspace"
3. Click "Allow"
4. **Copy the "Bot User OAuth Token"** (starts with `xoxb-`)
   - Example: `xoxb-XXXXXXXXXXXX-XXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXX`

### Step 4: Create/Choose a Slack Channel

1. In Slack, create a channel (e.g., `#p1-incidents`)
2. Right-click the channel → "View channel details"
3. Scroll down → **Copy the Channel ID** (starts with `C`)
   - Example: `C1234567890`

### Step 5: Configure Backend

Update your backend with the tokens:

**Option A: Using Environment Variables** (Recommended)

Create a `.env` file in the `backend` folder:
```
SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
SLACK_CHANNEL_ID=C1234567890
```

**Option B: Direct in Code**

In `backend/app.py`, replace these lines (around line 720):
```python
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")  # xoxb-...
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")  # C...
```

With:
```python
SLACK_BOT_TOKEN = "xoxb-YOUR-BOT-TOKEN-HERE"
SLACK_CHANNEL_ID = "C1234567890"
```

### Step 6: Restart Backend

```bash
cd c:\Users\fci\support_portal\support-portal\backend
python app.py
```

You should see:
```
✅ Slack Channel Manager initialized
```

## 📱 How It Works

### Creating New P1 Ticket:
1. User creates P1 ticket in frontend
2. Backend posts incident to Slack channel as a new thread
3. Thread contains: subject, merchant, user, description, status
4. `thread_ts` saved in database

### Sending Messages:
1. User types message in frontend chat
2. Backend adds message as a reply to the thread
3. Message visible in Slack immediately
4. All team members can see the conversation

### Reopening Old Tickets:
1. User opens old P1 ticket from "My Tickets"
2. Clicks "💬 Open Chat" button
3. All previous messages loaded from database
4. User can send new messages
5. New messages added to the same Slack thread
6. **WhatsApp-like experience**: continuous conversation!

### Viewing in Slack:
```
#p1-incidents

🚨 Payment Gateway Down
   Status: 🔴 Active
   Merchant: TechCorp
   User: John Doe
   3 replies ↓
   
   💬 User: Is the issue being looked at?
   👨‍💻 Operations: Yes, investigating now
   💬 User: Any ETA?
   
🚨 Database Timeout
   Status: ✅ Resolved
   Merchant: ShopifyPlus
   5 replies ↓
```

## 🎯 Benefits

✅ **Never lose context** - All conversations preserved in threads
✅ **Team collaboration** - Operations team sees everything in Slack
✅ **Easy handoff** - Any team member can pick up the conversation
✅ **History tracking** - Scroll through all past incidents
✅ **Professional** - Organized, clean, like enterprise messaging

## 🔄 Migration for Old Tickets

For existing P1 tickets without `thread_ts`:
- First message sent will create a new thread in Slack
- Future messages will use that thread
- Conversation continues normally

## 🧪 Testing

1. Create a new P1 ticket
2. Check Slack channel - should see the incident
3. Send a message from frontend
4. Check Slack - message should appear as a reply in the thread
5. Close the browser tab
6. Open the same P1 ticket again later
7. Send another message
8. Check Slack - message appears in the same thread!

## ❓ Troubleshooting

**"⚠️ Slack Channel Manager not available"**
- Make sure you set SLACK_BOT_TOKEN and SLACK_CHANNEL_ID
- Restart the backend server

**"Slack API error: channel_not_found"**
- Invite the bot to the channel: `/invite @P1 Incident Manager`
- Or use `chat:write.public` scope (already added above)

**"Slack API error: not_authed"**
- Check your bot token is correct
- Make sure it starts with `xoxb-`
- Reinstall app to workspace if needed

## 📚 Next Steps

Once this is working, you can:
- Add emoji reactions for status changes
- Implement auto-resolve when team types "resolved"
- Add buttons for quick actions
- Create summary reports from Slack history
