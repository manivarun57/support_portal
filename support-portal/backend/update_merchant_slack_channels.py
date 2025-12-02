#!/usr/bin/env python3
"""
Update Slack Channel IDs for Merchants
This script reads from environment variables and updates the merchants table
"""

import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_merchant_channels():
    """Update merchant Slack channel IDs from environment variables"""
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    print("=" * 70)
    print("UPDATING MERCHANT SLACK CHANNELS")
    print("=" * 70)
    
    # Get merchants
    cursor.execute("SELECT merchant_id, merchant_name, company_name FROM merchants")
    merchants = cursor.fetchall()
    
    # Channel mapping from environment variables
    channel_mapping = {
        'techcorp': os.getenv('SLACK_CHANNEL_TECHCORP', ''),
        'shopifyplus': os.getenv('SLACK_CHANNEL_SHOPIFYPLUS', ''),
        'financeone': os.getenv('SLACK_CHANNEL_FINANCEONE', '')
    }
    
    print("\n📋 Environment Variables:")
    for merchant_name, channel_id in channel_mapping.items():
        status = "✅ SET" if channel_id else "❌ NOT SET"
        print(f"   SLACK_CHANNEL_{merchant_name.upper()}: {status}")
        if channel_id:
            print(f"      → {channel_id}")
    
    print("\n" + "=" * 70)
    print("UPDATING DATABASE")
    print("=" * 70)
    
    updated_count = 0
    for merchant_id, merchant_name, company_name in merchants:
        channel_id = channel_mapping.get(merchant_name, '')
        
        if channel_id:
            cursor.execute("""
                UPDATE merchants 
                SET slack_channel_id = ?
                WHERE merchant_id = ?
            """, (channel_id, merchant_id))
            print(f"✅ Updated {company_name} ({merchant_name})")
            print(f"   Channel ID: {channel_id}")
            updated_count += 1
        else:
            print(f"⚠️  Skipped {company_name} ({merchant_name}) - No channel ID in environment")
    
    conn.commit()
    
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    cursor.execute("""
        SELECT merchant_id, merchant_name, company_name, slack_channel_id 
        FROM merchants
    """)
    results = cursor.fetchall()
    
    for merchant_id, merchant_name, company_name, slack_channel_id in results:
        status = "✅" if slack_channel_id else "❌"
        print(f"{status} {company_name} ({merchant_name})")
        if slack_channel_id:
            print(f"   Channel: {slack_channel_id}")
        else:
            print(f"   Channel: Not configured")
        print()
    
    conn.close()
    
    print("=" * 70)
    print(f"✅ Updated {updated_count} merchant(s)")
    print("=" * 70)
    
    if updated_count == 0:
        print("""
⚠️  WARNING: No channels were updated!

Please add the following to your .env file:

SLACK_CHANNEL_TECHCORP=C1234567890
SLACK_CHANNEL_SHOPIFYPLUS=C2345678901
SLACK_CHANNEL_FINANCEONE=C3456789012

Replace with your actual Slack channel IDs.
""")

if __name__ == "__main__":
    update_merchant_channels()
