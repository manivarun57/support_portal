# 🔧 Complete Slack Integration Setup Guide

## Current Status
✅ **Working**: User can send messages TO Slack  
❌ **Not Working**: Operations team messages FROM Slack don't reach frontend

---

## 🎯 The Problem

Your frontend is sending messages to Slack successfully, but when operations team replies in Slack, those messages are not appearing in your frontend. This is because:

1. **Slack doesn't know where to send events** - You need to configure Slack Event Subscriptions
2. **Your backend needs a public URL** - Slack can't reach `localhost:8000`
3. **You need ngrok running** - To expose your local backend to the internet

---

## ✅ Step-by-Step Solution

### **Step 1: Start ngrok to expose your backend**

Open a PowerShell terminal and run:

```powershell
# Start ngrok on port 8000 (where your backend runs)
ngrok http 8000
```

You should see output like:
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8000
```

**IMPORTANT**: Copy the `https://abc123.ngrok-free.app` URL - you'll need it!

---

### **Step 2: Configure Slack App Event Subscriptions**

1. **Go to Slack API Dashboard**:
   - Visit: https://api.slack.com/apps
   - Find your app (or create one if needed)

2. **Enable Event Subscriptions**:
   - Click "Event Subscriptions" in left sidebar
   - Toggle "Enable Events" to ON

3. **Set Request URL**:
   ```
   https://YOUR-NGROK-URL.ngrok-free.app/api/slack/webhook
   ```
   Replace `YOUR-NGROK-URL` with your ngrok URL from Step 1

   Example: `https://abc123.ngrok-free.app/api/slack/webhook`

4. **Slack will verify the URL** - Your backend will respond to the challenge

5. **Subscribe to Bot Events**:
   Click "Subscribe to bot events" and add:
   - `message.channels` - To receive messages from public channels
   - `message.groups` - To receive messages from private channels
   - `message.im` - To receive direct messages

6. **Save Changes** - Click "Save Changes" at the bottom

7. **Reinstall App** (if prompted):
   - Click "Reinstall App" to apply new permissions
   - Authorize the app

---

### **Step 3: Update Slack Channel Webhook (if needed)**

Make sure the P1 incidents are using a valid Slack webhook URL:

1. Go to: https://api.slack.com/apps
2. Click your app → "Incoming Webhooks"
3. Copy the webhook URL (should look like): 
   ```
   <your-slack-webhook-url>
   ```

This is already in your code, so you should be good!

---

### **Step 4: Test the Complete Flow**

#### **A. Start Backend**
```powershell
cd c:\Users\fci\support_portal\support-portal\backend
python app.py
```

Backend should be running on: `http://localhost:8000`

#### **B. Start ngrok (in another terminal)**
```powershell
ngrok http 8000
```

Keep this running! Don't close this terminal.

#### **C. Start Frontend (in another terminal)**
```powershell
cd c:\Users\fci\support_portal\support-portal\frontend
npm run dev
```

Frontend should be running on: `http://localhost:3000`

#### **D. Create a P1 Incident**
1. Go to: `http://localhost:3000/p1-critical`
2. Fill out the form and submit
3. **Check Slack** - You should see the P1 alert! ✅

#### **E. Send Message from Frontend**
1. On the success page, type a message: "Need urgent help!"
2. Click Send
3. **Check Slack** - Your message should appear! ✅

#### **F. Reply from Slack**
1. In your Slack workspace, find the channel (e.g., `#p1-incidents`)
2. Type a reply: "We're on it! Investigating now."
3. **Check Frontend** - Message should appear in chat within 5 seconds! ✅

---

## 🔍 Troubleshooting

### **Problem: Slack says "Failed to verify URL"**

**Cause**: Backend is not responding to Slack's verification challenge

**Fix**:
1. Check backend is running: `http://localhost:8000/health`
2. Check ngrok is running: Visit ngrok URL in browser
3. Check backend logs for errors
4. Test the webhook endpoint manually:
   ```powershell
   curl -X POST https://YOUR-NGROK-URL.ngrok-free.app/api/slack/webhook `
     -H "Content-Type: application/json" `
     -d '{"type":"url_verification","challenge":"test123"}'
   ```
   Should return: `{"challenge":"test123"}`

---

### **Problem: Messages from Slack not appearing in frontend**

**Possible causes**:

1. **Ngrok stopped running**
   - Check if ngrok terminal is still open
   - Restart: `ngrok http 8000`
   - Update Slack Event Subscriptions URL if ngrok URL changed

2. **Slack not sending events**
   - Go to Slack API → Your App → Event Subscriptions
   - Check "Request URL" is verified (green checkmark)
   - Check "Subscribe to Bot Events" includes `message.channels`

3. **Backend not processing events**
   - Check backend logs: `python app.py`
   - Look for: `📨 WEBHOOK CALLED` in logs
   - If you see this, events are arriving!

4. **Frontend not polling**
   - Open browser console (F12)
   - Look for: `🔄 Polling messages for incident:`
   - Should poll every 5 seconds

5. **Database not storing messages**
   - Check if `slack_messages` table exists:
     ```powershell
     cd c:\Users\fci\support_portal\support-portal\backend
     python check_db.py
     ```
   - Look for: `slack_messages` table

---

### **Problem: "Failed to send message to Slack"**

**Cause**: Webhook URL is invalid or expired

**Fix**:
1. Go to: https://api.slack.com/apps
2. Click your app → "Incoming Webhooks"
3. Regenerate webhook URL if needed
4. Update in backend code or database

---

### **Problem: Duplicate messages appearing**

**Cause**: Slack retries failed webhooks

**Fix**: Already handled! The code checks for duplicate message IDs.

---

## 🧪 Quick Test Commands

### **Test 1: Check Backend is Running**
```powershell
curl http://localhost:8000/health
```
Expected: `{"status":"ok","timestamp":"..."}`

### **Test 2: Check ngrok Tunnel**
```powershell
# Visit ngrok URL in browser
start https://YOUR-NGROK-URL.ngrok-free.app/health
```
Expected: Same health check response

### **Test 3: Manually Send Slack Event**
```powershell
curl -X POST https://YOUR-NGROK-URL.ngrok-free.app/api/slack/webhook `
  -H "Content-Type: application/json" `
  -d '{
    "type": "event_callback",
    "event": {
      "type": "message",
      "user": "U123",
      "text": "Test message from Slack",
      "channel": "C07V57P5N31",
      "ts": "1234567890.123456"
    }
  }'
```

Expected: `{"status":"ok"}`

Then check frontend - message should appear!

### **Test 4: Check Database Messages**
```powershell
cd c:\Users\fci\support_portal\support-portal\backend
python -c "import sqlite3; conn = sqlite3.connect('tickets.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM slack_messages'); print(cursor.fetchall())"
```

---

## 📋 Complete Setup Checklist

- [ ] Backend running on `http://localhost:8000`
- [ ] ngrok running and exposing backend: `ngrok http 8000`
- [ ] Slack App created at https://api.slack.com/apps
- [ ] Incoming Webhooks enabled and URL copied
- [ ] Event Subscriptions enabled
- [ ] Request URL set to: `https://YOUR-NGROK-URL/api/slack/webhook`
- [ ] Request URL verified (green checkmark in Slack)
- [ ] Bot events subscribed: `message.channels`
- [ ] App reinstalled (if permissions changed)
- [ ] Frontend running on `http://localhost:3000`
- [ ] Can create P1 incident and see alert in Slack
- [ ] Can send message from frontend to Slack
- [ ] Can reply in Slack and see message in frontend

---

## 🚀 Production Deployment Notes

When deploying to production:

1. **Replace ngrok with real domain**:
   - Deploy backend to AWS/Azure/Heroku
   - Use your domain: `https://api.yourcompany.com`
   - Update Slack Event Subscriptions URL

2. **Secure the webhook endpoint**:
   - Add Slack signature verification
   - Check `X-Slack-Signature` header
   - Use `X-Slack-Request-Timestamp` to prevent replays

3. **Add rate limiting**:
   - Prevent message spam
   - Use Redis for rate limit tracking

4. **Use WebSocket instead of polling**:
   - Real-time updates without 5-second delay
   - More efficient than HTTP polling

---

## 📞 Need Help?

1. **Check backend logs**: Look for `📨 WEBHOOK CALLED` when Slack sends events
2. **Check browser console**: Look for `🔄 Polling messages` every 5 seconds
3. **Check Slack logs**: Go to Slack API → Your App → Event Subscriptions → View Logs
4. **Test webhook manually**: Use curl commands above

---

## 🎉 Success Criteria

You'll know it's working when:

1. ✅ You create P1 incident → Alert appears in Slack
2. ✅ You send message from frontend → Message appears in Slack
3. ✅ Ops team replies in Slack → Reply appears in frontend within 5 seconds
4. ✅ Message history persists across page refreshes
5. ✅ Multiple users can chat in the same incident channel

---

## 🔐 Security Best Practices

1. **Don't commit secrets**: Keep webhook URLs in environment variables
2. **Verify Slack requests**: Check signatures on webhook calls
3. **Rate limit**: Prevent abuse of message endpoints
4. **Audit log**: Track all communications for compliance
5. **HTTPS only**: Never use HTTP in production

---

Good luck! If you follow these steps, your Slack integration will work perfectly! 🚀
