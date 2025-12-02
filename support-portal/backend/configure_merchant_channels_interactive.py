#!/usr/bin/env python3
"""
Example: Manually Set Slack Channels for Testing
This script demonstrates how to manually configure Slack channels for each merchant
Use this if you want to test with temporary channel IDs
"""

import sqlite3

def set_test_channels():
    """
    Set example/test Slack channel IDs for each merchant
    Replace these with your actual Slack channel IDs
    """
    
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("MANUALLY CONFIGURE SLACK CHANNELS")
    print("=" * 80)
    print("\n⚠️  WARNING: This script will directly update the database")
    print("Make sure you have your actual Slack channel IDs ready!\n")
    
    # Get current merchants
    cursor.execute("SELECT merchant_id, merchant_name, company_name FROM merchants")
    merchants = cursor.fetchall()
    
    print("Found merchants:")
    for merchant_id, merchant_name, company_name in merchants:
        print(f"  - {company_name} ({merchant_name}): {merchant_id}")
    
    print("\n" + "-" * 80)
    print("CONFIGURATION OPTIONS")
    print("-" * 80)
    print("\nOption 1: Use the SAME channel for all merchants (for testing)")
    print("Option 2: Use DIFFERENT channels for each merchant (production setup)")
    print()
    
    choice = input("Enter option (1 or 2): ").strip()
    
    if choice == "1":
        # Use same channel for all
        channel_id = input("\nEnter Slack Channel ID (e.g., C0A10UFAT9N): ").strip()
        
        if not channel_id.startswith('C'):
            print("❌ Invalid channel ID format (should start with 'C')")
            return
        
        print(f"\n📝 Setting channel {channel_id} for ALL merchants...")
        
        for merchant_id, merchant_name, company_name in merchants:
            cursor.execute("""
                UPDATE merchants 
                SET slack_channel_id = ?
                WHERE merchant_id = ?
            """, (channel_id, merchant_id))
            print(f"✅ Updated {company_name}")
        
        conn.commit()
        print(f"\n✅ All merchants configured to use channel: {channel_id}")
        
    elif choice == "2":
        # Use different channels
        print("\n📝 Enter Slack Channel ID for each merchant:")
        print("   (Format: C1234567890)\n")
        
        updates = []
        
        for merchant_id, merchant_name, company_name in merchants:
            channel_id = input(f"{company_name} ({merchant_name}) → Channel ID: ").strip()
            
            if not channel_id:
                print(f"   ⏭️  Skipping {company_name}")
                continue
            
            if not channel_id.startswith('C'):
                print(f"   ⚠️  Warning: Channel ID should start with 'C'")
                confirm = input("   Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    print(f"   ⏭️  Skipping {company_name}")
                    continue
            
            updates.append((channel_id, merchant_id, company_name))
        
        if not updates:
            print("\n❌ No channels to update")
            return
        
        print(f"\n📋 Will update {len(updates)} merchant(s):")
        for channel_id, merchant_id, company_name in updates:
            print(f"   {company_name} → {channel_id}")
        
        confirm = input("\nProceed with updates? (y/n): ").strip().lower()
        
        if confirm == 'y':
            for channel_id, merchant_id, company_name in updates:
                cursor.execute("""
                    UPDATE merchants 
                    SET slack_channel_id = ?
                    WHERE merchant_id = ?
                """, (channel_id, merchant_id))
                print(f"✅ Updated {company_name}")
            
            conn.commit()
            print(f"\n✅ Successfully updated {len(updates)} merchant(s)")
        else:
            print("\n❌ Update cancelled")
    
    else:
        print("\n❌ Invalid option")
        return
    
    # Show results
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    cursor.execute("""
        SELECT merchant_name, company_name, slack_channel_id 
        FROM merchants
        ORDER BY merchant_name
    """)
    
    results = cursor.fetchall()
    for merchant_name, company_name, slack_channel_id in results:
        status = "✅" if slack_channel_id else "❌"
        print(f"{status} {company_name}: {slack_channel_id or 'NOT SET'}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ CONFIGURATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Make sure your Slack bot is invited to all configured channels")
    print("2. Test by creating a P1 incident for each merchant")
    print("3. Verify messages appear in the correct channels")
    print("\nTo view current configuration:")
    print("  python view_slack_configuration.py")

if __name__ == "__main__":
    try:
        set_test_channels()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
