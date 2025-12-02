#!/usr/bin/env python3
"""
Database Migration: Add Slack Channel Support for Merchants
This script adds slack_channel_id column to merchants table
and sets up environment variables for client-specific channels
"""

import sqlite3
import os
from datetime import datetime

def migrate_merchants_table():
    """Add slack_channel_id column to merchants table"""
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    print("=" * 70)
    print("ADDING SLACK CHANNEL SUPPORT TO MERCHANTS TABLE")
    print("=" * 70)
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(merchants)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'slack_channel_id' in columns:
        print("✅ slack_channel_id column already exists")
    else:
        print("📝 Adding slack_channel_id column to merchants table...")
        cursor.execute("""
            ALTER TABLE merchants 
            ADD COLUMN slack_channel_id TEXT
        """)
        conn.commit()
        print("✅ Column added successfully")
    
    # Display current merchants
    cursor.execute("SELECT merchant_id, merchant_name, company_name FROM merchants")
    merchants = cursor.fetchall()
    
    print("\n" + "=" * 70)
    print("CURRENT MERCHANTS")
    print("=" * 70)
    for merchant in merchants:
        print(f"ID: {merchant[0]}")
        print(f"Name: {merchant[1]}")
        print(f"Company: {merchant[2]}")
        print("-" * 70)
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("NEXT STEPS: CONFIGURE SLACK CHANNELS")
    print("=" * 70)
    print("""
For each client, you need to:

1. CREATE DEDICATED SLACK CHANNELS:
   - #techcorp-p1-incidents (for TechCorp Inc.)
   - #shopifyplus-p1-incidents (for ShopifyPlus Ltd.)
   - #financeone-p1-incidents (for FinanceOne Corporation)

2. GET CHANNEL IDs:
   - Right-click on each channel in Slack
   - Select "View channel details"
   - Copy the Channel ID (e.g., C1234567890)

3. UPDATE ENVIRONMENT VARIABLES:
   Add to your .env file:
   
   SLACK_CHANNEL_TECHCORP=C1234567890
   SLACK_CHANNEL_SHOPIFYPLUS=C2345678901
   SLACK_CHANNEL_FINANCEONE=C3456789012

4. UPDATE MERCHANTS IN DATABASE:
   Run: python update_merchant_slack_channels.py

OR you can manually update:
   UPDATE merchants SET slack_channel_id='C1234567890' 
   WHERE merchant_id='merchant_510eaea5f65f';
   
   UPDATE merchants SET slack_channel_id='C2345678901' 
   WHERE merchant_id='merchant_c4fd34b3f1a1';
   
   UPDATE merchants SET slack_channel_id='C3456789012' 
   WHERE merchant_id='merchant_6cf4fd72c84a';
""")

if __name__ == "__main__":
    migrate_merchants_table()
