# Multi-Client Slack Channel Configuration Guide

## Overview

This guide explains how to configure separate Slack channels for each client (merchant) in the Support Portal. Each of your 3 clients will have their own dedicated Slack channel where P1 Critical incidents are automatically posted.

## Current Merchants

You have 3 merchants configured:

1. **TechCorp Inc.** (`merchant_id: merchant_510eaea5f65f`, `merchant_name: techcorp`)
2. **ShopifyPlus Ltd.** (`merchant_id: merchant_c4fd34b3f1a1`, `merchant_name: shopifyplus`)
3. **FinanceOne Corporation** (`merchant_id: merchant_6cf4fd72c84a`, `merchant_name: financeone`)

## Architecture

### How It Works

```
User creates P1 ticket → System identifies merchant → Routes to merchant's Slack channel
                                     ↓
                         Each merchant has dedicated channel:
                         - #techcorp-p1-incidents
                         - #shopifyplus-p1-incidents
                         - #financeone-p1-incidents
```

### Database Structure

The `merchants` table now includes a `slack_channel_id` column:
```sql
ALTER TABLE merchants ADD COLUMN slack_channel_id TEXT;
```

### Code Changes

1. **SlackChannelManager** - Now supports dynamic channel routing based on merchant_id
2. **app.py** - P1 incident creation includes merchant_id for channel routing
3. **Database connection** - Passed to SlackChannelManager for merchant lookup

---

## Setup Instructions

### Step 1: Create Slack Channels

Create 3 dedicated Slack channels in your workspace:

1. `#techcorp-p1-incidents`
2. `#shopifyplus-p1-incidents`
3. `#financeone-p1-incidents`

**To create a channel:**
- Click the ➕ next to "Channels" in Slack
- Select "Create a channel"
- Name it according to the pattern above
- Set as Public or Private (recommend Private for security)
- Add relevant team members

### Step 2: Get Channel IDs

For each channel:

1. Right-click on the channel name
2. Select **"View channel details"**
3. Scroll down to find the **Channel ID**
4. Copy the ID (format: `C1234567890`)

You should now have 3 channel IDs like:
- TechCorp: `C08V57MBF9J`
- ShopifyPlus: `C08VB8X3K2L`
- FinanceOne: `C08VA9Y4M5N`

### Step 3: Update Environment Variables

Add the following to your `.env` file in the `backend` directory:

```bash
# Slack Bot Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# Default channel (optional - used as fallback)
SLACK_CHANNEL_ID=C1234567890

# Merchant-specific channels
SLACK_CHANNEL_TECHCORP=C08V57MBF9J
SLACK_CHANNEL_SHOPIFYPLUS=C08VB8X3K2L
SLACK_CHANNEL_FINANCEONE=C08VA9Y4M5N
```

### Step 4: Update Database

Run the update script to populate channel IDs in the database:

```bash
cd support-portal/backend
python update_merchant_slack_channels.py
```

This script will:
- Read channel IDs from environment variables
- Update the `merchants` table with corresponding channel IDs
- Display verification of the updates

**Output should show:**
```
✅ Updated TechCorp Inc. (techcorp)
   Channel ID: C08V57MBF9J
✅ Updated ShopifyPlus Ltd. (shopifyplus)
   Channel ID: C08VB8X3K2L
✅ Updated FinanceOne Corporation (financeone)
   Channel ID: C08VA9Y4M5N
```

### Step 5: Verify Configuration

Check that channels are properly configured:

```bash
python -c "import sqlite3; conn = sqlite3.connect('support_portal.db'); cursor = conn.cursor(); cursor.execute('SELECT merchant_name, company_name, slack_channel_id FROM merchants'); [print(f'{row[1]}: {row[2] or \"NOT SET\"}') for row in cursor.fetchall()]"
```

### Step 6: Restart Backend Server

Restart your backend server to load the new configuration:

```bash
# Stop the current server (Ctrl+C)
# Then start again:
python app.py
```

You should see:
```
✅ Slack Channel Manager initialized with multi-client support
```

---

## Testing

### Test Each Merchant's Channel

Create test P1 incidents for each merchant:

1. **Login as TechCorp user:**
   ```
   Username: admin@techcorp.com
   Password: (your password)
   ```
   Create a P1 ticket → Should post to `#techcorp-p1-incidents`

2. **Login as ShopifyPlus user:**
   ```
   Username: support@shopifyplus.com
   Password: (your password)
   ```
   Create a P1 ticket → Should post to `#shopifyplus-p1-incidents`

3. **Login as FinanceOne user:**
   ```
   Username: contact@financeone.com
   Password: (your password)
   ```
   Create a P1 ticket → Should post to `#financeone-p1-incidents`

---

## Slack Bot Permissions

Your Slack bot needs these permissions (OAuth & Permissions):

### Required Scopes:
- `chat:write` - Post messages to channels
- `chat:write.public` - Post to public channels without joining
- `channels:history` - View messages in public channels
- `channels:read` - View basic channel info

### For Private Channels:
- `groups:write` - Post to private channels
- `groups:history` - View messages in private channels
- `groups:read` - View private channel info

---

## Troubleshooting

### Issue: P1 incidents not posting to Slack

**Check:**
1. Verify `SLACK_BOT_TOKEN` is set correctly
2. Verify channel IDs are correct in database
3. Check bot has been invited to all 3 channels
4. Review backend logs for error messages

**Invite bot to channels:**
```
In each Slack channel:
1. Type: /invite @YourBotName
2. The bot should appear in the channel member list
```

### Issue: All incidents go to default channel

**Cause:** merchant_id not being passed correctly

**Fix:**
1. Verify user is logged in with proper authentication
2. Check that `user_info.get('merchant_id')` is populated
3. Verify database has `slack_channel_id` for each merchant

### Issue: Channel IDs not updating

**Solution:**
```bash
# Manual update:
sqlite3 support_portal.db
UPDATE merchants SET slack_channel_id='C08V57MBF9J' WHERE merchant_id='merchant_510eaea5f65f';
UPDATE merchants SET slack_channel_id='C08VB8X3K2L' WHERE merchant_id='merchant_c4fd34b3f1a1';
UPDATE merchants SET slack_channel_id='C08VA9Y4M5N' WHERE merchant_id='merchant_6cf4fd72c84a';
.exit
```

---

## How Messages Are Routed

### Flow Diagram:

```
1. User creates P1 ticket
   ↓
2. System extracts user's merchant_id from authentication
   ↓
3. SlackChannelManager.post_incident() called with incident data including merchant_id
   ↓
4. get_merchant_channel(merchant_id) queries database for slack_channel_id
   ↓
5. If merchant has channel → Post to merchant's channel
   If not → Post to default channel (fallback)
   ↓
6. Slack message posted with @here notification to operations team
```

### Code Reference:

**In `slack_channel_manager.py`:**
```python
def get_merchant_channel(self, merchant_id: str) -> str:
    """Get the Slack channel ID for a specific merchant"""
    # Query database for merchant's channel
    # Return merchant's channel or default
```

**In `app.py`:**
```python
ticket_dict['merchant_id'] = user_info.get('merchant_id', None)
thread_ts = slack_channel_manager.post_incident(ticket_dict)
```

---

## Benefits of Multi-Client Slack Channels

✅ **Isolation** - Each client's incidents are isolated in their own channel
✅ **Security** - Private channels prevent cross-client information leakage
✅ **Team-specific** - Add different operations team members to different channels
✅ **Better organization** - Easy to track P1 incidents per client
✅ **Scalable** - Easy to add more clients - just create channel and update config

---

## Adding New Clients

When adding a new merchant:

1. **Create merchant in database:**
   ```python
   # Use the /auth/merchants endpoint or directly in DB
   ```

2. **Create Slack channel:**
   - Name: `#{merchant_name}-p1-incidents`
   - Get Channel ID

3. **Add to .env:**
   ```bash
   SLACK_CHANNEL_NEWCLIENT=C1234567890
   ```

4. **Update database:**
   ```bash
   python update_merchant_slack_channels.py
   ```

5. **Restart backend server**

---

## Support

For issues or questions:
- Check backend logs for error messages
- Verify Slack bot permissions
- Test with a manual Slack API call
- Review merchant configuration in database

## Files Modified

- `slack_channel_manager.py` - Added multi-client routing support
- `app.py` - Pass merchant_id and database connection
- `add_merchant_slack_channels.py` - Migration script
- `update_merchant_slack_channels.py` - Update script
- `MULTI_CLIENT_SLACK_SETUP.md` - This documentation
