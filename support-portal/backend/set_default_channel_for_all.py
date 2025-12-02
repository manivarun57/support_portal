#!/usr/bin/env python3
"""
Quick Setup: Use the same Slack channel for all merchants
This uses your existing SLACK_CHANNEL_ID for all 3 merchants
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def set_default_channel_for_all():
    """Set the default channel from .env for all merchants"""
    
    default_channel = os.getenv('SLACK_CHANNEL_ID', '')
    
    if not default_channel:
        print("❌ ERROR: SLACK_CHANNEL_ID not found in .env file")
        print("Please set SLACK_CHANNEL_ID in your .env file")
        return
    
    print("=" * 80)
    print("QUICK SETUP: USE SAME CHANNEL FOR ALL MERCHANTS")
    print("=" * 80)
    print(f"\nUsing channel: {default_channel}")
    print("This will configure all 3 merchants to use the same Slack channel.")
    print("(You can create separate channels later)\n")
    
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    # Get all merchants
    cursor.execute("SELECT merchant_id, merchant_name, company_name FROM merchants")
    merchants = cursor.fetchall()
    
    if not merchants:
        print("❌ No merchants found in database")
        conn.close()
        return
    
    print(f"Found {len(merchants)} merchants:")
    for merchant_id, merchant_name, company_name in merchants:
        print(f"  • {company_name} ({merchant_name})")
    
    print(f"\n✅ Setting channel {default_channel} for all merchants...")
    
    # Update all merchants
    for merchant_id, merchant_name, company_name in merchants:
        cursor.execute("""
            UPDATE merchants 
            SET slack_channel_id = ?
            WHERE merchant_id = ?
        """, (default_channel, merchant_id))
        print(f"   ✅ {company_name}")
    
    conn.commit()
    
    # Verify
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    cursor.execute("""
        SELECT merchant_name, company_name, slack_channel_id 
        FROM merchants
        ORDER BY merchant_name
    """)
    
    results = cursor.fetchall()
    all_configured = True
    
    for merchant_name, company_name, slack_channel_id in results:
        if slack_channel_id:
            print(f"✅ {company_name}: {slack_channel_id}")
        else:
            print(f"❌ {company_name}: NOT SET")
            all_configured = False
    
    conn.close()
    
    if all_configured:
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! All merchants configured!")
        print("=" * 80)
        print(f"\nAll P1 incidents will now post to: {default_channel}")
        print("\nNext steps:")
        print("1. Make sure your Slack bot is invited to the channel")
        print("2. Test by creating P1 incidents for each merchant")
        print("3. All incidents will appear in the same channel for now")
        print("\nTo create separate channels later:")
        print("- Create new Slack channels for each merchant")
        print("- Run: python configure_merchant_channels_interactive.py")
    else:
        print("\n❌ Some merchants were not configured properly")

if __name__ == "__main__":
    set_default_channel_for_all()
