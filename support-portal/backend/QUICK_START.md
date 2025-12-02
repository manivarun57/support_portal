# Multi-Client Slack Integration - Quick Start

## What Was Implemented

Your Support Portal now supports **separate Slack channels for each of your 3 clients**:

1. **TechCorp Inc.** → Will have dedicated channel
2. **ShopifyPlus Ltd.** → Will have dedicated channel  
3. **FinanceOne Corporation** → Will have dedicated channel

## How It Works

```
User (TechCorp) creates P1 incident → Posts to #techcorp-p1-incidents
User (ShopifyPlus) creates P1 incident → Posts to #shopifyplus-p1-incidents
User (FinanceOne) creates P1 incident → Posts to #financeone-p1-incidents
```

Each client's P1 Critical incidents are automatically routed to their own Slack channel, keeping communications isolated and organized.

---

## Quick Setup (3 Steps)

### Step 1: Create Slack Channels

In your Slack workspace, create 3 channels:
- `#techcorp-p1-incidents`
- `#shopifyplus-p1-incidents`
- `#financeone-p1-incidents`

Get each channel's ID (right-click → View channel details)

### Step 2: Configure Channels

**Option A: Interactive Setup (Easiest)**
```bash
cd support-portal/backend
python configure_merchant_channels_interactive.py
```

**Option B: Environment Variables**
```bash
# Add to .env file:
SLACK_CHANNEL_TECHCORP=C1234567890
SLACK_CHANNEL_SHOPIFYPLUS=C2345678901
SLACK_CHANNEL_FINANCEONE=C3456789012

# Then run:
python update_merchant_slack_channels.py
```

**Option C: Use Same Channel for Testing**
```bash
# Use your existing channel for all merchants:
python configure_merchant_channels_interactive.py
# Choose option 1, enter your existing channel ID
```

### Step 3: Verify Configuration

```bash
python view_slack_configuration.py
```

Should show all 3 merchants with ✅ CONFIGURED status.

---

## Testing

1. **Login as TechCorp user**
   - Email: `admin@techcorp.com`
   - Create a P1 ticket
   - Check `#techcorp-p1-incidents` channel

2. **Login as ShopifyPlus user**
   - Email: `support@shopifyplus.com`
   - Create a P1 ticket
   - Check `#shopifyplus-p1-incidents` channel

3. **Login as FinanceOne user**
   - Email: `contact@financeone.com`
   - Create a P1 ticket
   - Check `#financeone-p1-incidents` channel

---

## Files Created/Modified

### New Files:
- `MULTI_CLIENT_SLACK_SETUP.md` - Complete documentation
- `add_merchant_slack_channels.py` - Database migration
- `update_merchant_slack_channels.py` - Update from .env
- `view_slack_configuration.py` - View current config
- `configure_merchant_channels_interactive.py` - Interactive setup
- `QUICK_START.md` - This file

### Modified Files:
- `slack_channel_manager.py` - Added multi-client routing
- `app.py` - Pass merchant_id for routing

---

## Helper Scripts

| Script | Purpose |
|--------|---------|
| `view_slack_configuration.py` | Check current configuration |
| `configure_merchant_channels_interactive.py` | Interactive setup wizard |
| `update_merchant_slack_channels.py` | Update from .env file |
| `add_merchant_slack_channels.py` | Add database column (already done) |

---

## Architecture

### Before (Single Channel):
```
All P1 incidents → #p1-incidents channel
```

### After (Multi-Client):
```
TechCorp P1 → #techcorp-p1-incidents
ShopifyPlus P1 → #shopifyplus-p1-incidents  
FinanceOne P1 → #financeone-p1-incidents
```

### Database:
```sql
merchants table:
- merchant_id
- merchant_name
- company_name
- slack_channel_id  ← NEW COLUMN
```

### Code Flow:
```
1. User creates P1 ticket
2. System gets user's merchant_id from authentication
3. SlackChannelManager queries database for merchant's channel
4. Posts incident to merchant-specific channel
5. Falls back to default channel if not configured
```

---

## Important Notes

✅ **Backwards Compatible** - If channels aren't configured, falls back to default channel

✅ **Secure** - Each client only sees their own incidents

✅ **Scalable** - Easy to add more clients

✅ **Tested** - Code changes are minimal and focused

⚠️ **Remember** - Invite your Slack bot to all 3 channels:
```
In each channel: /invite @YourBotName
```

---

## Troubleshooting

**Issue:** Incidents not posting
- Check: `python view_slack_configuration.py`
- Verify bot is in all channels
- Check backend logs

**Issue:** All go to default channel
- Verify channels are configured in database
- Check user authentication includes merchant_id

**Quick Fix:**
```bash
# Reconfigure everything:
python configure_merchant_channels_interactive.py
python view_slack_configuration.py
# Restart backend server
```

---

## Need Help?

See detailed documentation: `MULTI_CLIENT_SLACK_SETUP.md`

Run diagnostic: `python view_slack_configuration.py`

Check backend logs when creating P1 tickets
