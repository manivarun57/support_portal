#!/usr/bin/env python3
"""
View Current Multi-Client Slack Configuration
Displays all merchants and their configured Slack channels
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def view_configuration():
    """Display current multi-client Slack configuration"""
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("MULTI-CLIENT SLACK CONFIGURATION")
    print("=" * 80)
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(merchants)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'slack_channel_id' not in columns:
        print("❌ ERROR: slack_channel_id column does not exist!")
        print("   Run: python add_merchant_slack_channels.py")
        conn.close()
        return
    
    print("\n📋 SLACK BOT CONFIGURATION")
    print("-" * 80)
    bot_token = os.getenv('SLACK_BOT_TOKEN', '')
    default_channel = os.getenv('SLACK_CHANNEL_ID', '')
    
    print(f"Bot Token: {'✅ Configured' if bot_token else '❌ NOT SET'}")
    if bot_token:
        print(f"  → {bot_token[:20]}...")
    
    print(f"Default Channel: {'✅ Set' if default_channel else '⚠️  Optional'}")
    if default_channel:
        print(f"  → {default_channel}")
    
    print("\n📊 MERCHANTS AND THEIR SLACK CHANNELS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT merchant_id, merchant_name, company_name, email, status, slack_channel_id
        FROM merchants
        ORDER BY merchant_name
    """)
    
    merchants = cursor.fetchall()
    
    if not merchants:
        print("❌ No merchants found in database")
        conn.close()
        return
    
    for idx, (merchant_id, merchant_name, company_name, email, status, slack_channel_id) in enumerate(merchants, 1):
        # Check if channel is in environment
        env_var_name = f"SLACK_CHANNEL_{merchant_name.upper()}"
        env_channel = os.getenv(env_var_name, '')
        
        status_emoji = "✅" if slack_channel_id else "❌"
        status_text = "CONFIGURED" if slack_channel_id else "NOT CONFIGURED"
        
        print(f"\n{idx}. {status_emoji} {company_name}")
        print(f"   Merchant Name: {merchant_name}")
        print(f"   Merchant ID: {merchant_id}")
        print(f"   Email: {email}")
        print(f"   Status: {status}")
        print(f"   Database Channel ID: {slack_channel_id or 'NOT SET'}")
        print(f"   Environment Variable: {env_var_name}")
        print(f"   Environment Value: {env_channel or 'NOT SET'}")
        
        # Check if they match
        if slack_channel_id and env_channel:
            if slack_channel_id == env_channel:
                print(f"   ✅ Database and environment match")
            else:
                print(f"   ⚠️  WARNING: Database and environment don't match!")
                print(f"      Database: {slack_channel_id}")
                print(f"      .env file: {env_channel}")
        elif not slack_channel_id and env_channel:
            print(f"   ⚠️  Channel in .env but not in database - run update script")
        elif slack_channel_id and not env_channel:
            print(f"   ⚠️  Channel in database but not in .env - add to .env file")
        
        print("-" * 80)
    
    conn.close()
    
    # Summary
    configured_count = sum(1 for m in merchants if m[5])  # slack_channel_id is index 5
    total_count = len(merchants)
    
    print("\n📈 SUMMARY")
    print("=" * 80)
    print(f"Total Merchants: {total_count}")
    print(f"Configured Channels: {configured_count}")
    print(f"Not Configured: {total_count - configured_count}")
    
    if configured_count == total_count:
        print("\n🎉 ✅ ALL MERCHANTS HAVE SLACK CHANNELS CONFIGURED!")
    elif configured_count > 0:
        print(f"\n⚠️  {total_count - configured_count} merchant(s) still need configuration")
        print("   Run: python update_merchant_slack_channels.py")
    else:
        print("\n❌ NO MERCHANTS CONFIGURED")
        print("\nNext steps:")
        print("1. Create Slack channels for each merchant")
        print("2. Get channel IDs")
        print("3. Add to .env file:")
        for m in merchants:
            merchant_name = m[1]
            print(f"   SLACK_CHANNEL_{merchant_name.upper()}=C1234567890")
        print("4. Run: python update_merchant_slack_channels.py")
    
    print("\n" + "=" * 80)
    print("For detailed setup instructions, see: MULTI_CLIENT_SLACK_SETUP.md")
    print("=" * 80)

if __name__ == "__main__":
    view_configuration()
