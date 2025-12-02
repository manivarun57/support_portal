# Quick Setup: Enable Slack ↔ Frontend Communication

## The Problem
- Your backend is on `localhost:8000`
- Slack cannot reach localhost from the internet
- So when operations team types "resolved" in Slack, your backend never receives it

## The Solution: Use ngrok

### Step 1: Start ngrok
```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copy that HTTPS URL** (e.g., `https://abc123.ngrok-free.app`)

### Step 2: Configure Slack Event Subscriptions

1. Go to https://api.slack.com/apps
2. Select your app (or create one)
3. Go to "Event Subscriptions"
4. Turn it **ON**
5. Request URL: `https://YOUR-NGROK-URL.ngrok-free.app/api/slack/webhook`
   Example: `https://abc123.ngrok-free.app/api/slack/webhook`
6. Subscribe to bot events:
   - `message.channels`
   - `message.groups`
7. Save Changes

### Step 3: Get a New Webhook URL for Sending to Slack

1. In the same Slack app, go to "Incoming Webhooks"
2. Turn it **ON**
3. Click "Add New Webhook to Workspace"
4. Select the channel (e.g., #support-portal)
5. **Copy the webhook URL**

### Step 4: Update Your Backend

Run this command to update the webhook URL in your code:

```bash
# Replace YOUR_NEW_WEBHOOK_URL with the URL from Step 3
```

Then restart your backend server.

### Step 5: Test It

1. Create a P1 ticket in your app
2. Check Slack - you should see the notification
3. Reply in Slack with any message
4. Check your frontend - the message should appear
5. Type "resolved" in Slack
6. Frontend should show the incident as resolved

## Note
Keep ngrok running in a terminal while testing. If you stop it, Slack won't be able to reach your backend.
