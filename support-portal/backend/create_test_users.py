#!/usr/bin/env python3
"""
Create Test Merchants and Users
Run this script to populate the database with test data
"""

import sys
from shared import DatabaseManager
from auth_models import AuthManager

def create_test_data():
    """Create test merchants and users"""
    
    print("🚀 Creating test merchants and users...")
    print("=" * 60)
    
    db_manager = DatabaseManager()
    auth_manager = AuthManager(db_manager)
    
    # Test Merchant 1: Tech Startup
    print("\n📦 Creating Merchant 1: TechCorp")
    merchant1 = auth_manager.create_merchant(
        merchant_name="techcorp",
        company_name="TechCorp Inc.",
        email="admin@techcorp.com",
        phone="+1-555-0101"
    )
    print(f"✅ Merchant created: {merchant1.merchant_name}")
    print(f"   Merchant ID: {merchant1.merchant_id}")
    print(f"   API Key: {merchant1.api_key}")
    
    # Users for TechCorp
    print("\n👤 Creating users for TechCorp:")
    
    user1 = auth_manager.create_user(
        merchant_id=merchant1.merchant_id,
        username="john.doe",
        email="john.doe@techcorp.com",
        password="password123",
        full_name="John Doe",
        role="admin"
    )
    print(f"   ✅ {user1.full_name} (@{user1.username}) - {user1.role}")
    print(f"      User ID: {user1.user_id}")
    print(f"      Login: john.doe / password123")
    
    user2 = auth_manager.create_user(
        merchant_id=merchant1.merchant_id,
        username="sarah.smith",
        email="sarah.smith@techcorp.com",
        password="password123",
        full_name="Sarah Smith",
        role="user"
    )
    print(f"   ✅ {user2.full_name} (@{user2.username}) - {user2.role}")
    print(f"      User ID: {user2.user_id}")
    print(f"      Login: sarah.smith / password123")
    
    user3 = auth_manager.create_user(
        merchant_id=merchant1.merchant_id,
        username="mike.johnson",
        email="mike.johnson@techcorp.com",
        password="password123",
        full_name="Mike Johnson",
        role="user"
    )
    print(f"   ✅ {user3.full_name} (@{user3.username}) - {user3.role}")
    print(f"      User ID: {user3.user_id}")
    print(f"      Login: mike.johnson / password123")
    
    # Test Merchant 2: E-commerce Company
    print("\n📦 Creating Merchant 2: ShopifyPlus")
    merchant2 = auth_manager.create_merchant(
        merchant_name="shopifyplus",
        company_name="ShopifyPlus Ltd.",
        email="support@shopifyplus.com",
        phone="+1-555-0202"
    )
    print(f"✅ Merchant created: {merchant2.merchant_name}")
    print(f"   Merchant ID: {merchant2.merchant_id}")
    print(f"   API Key: {merchant2.api_key}")
    
    # Users for ShopifyPlus
    print("\n👤 Creating users for ShopifyPlus:")
    
    user4 = auth_manager.create_user(
        merchant_id=merchant2.merchant_id,
        username="alice.wong",
        email="alice.wong@shopifyplus.com",
        password="password123",
        full_name="Alice Wong",
        role="admin"
    )
    print(f"   ✅ {user4.full_name} (@{user4.username}) - {user4.role}")
    print(f"      User ID: {user4.user_id}")
    print(f"      Login: alice.wong / password123")
    
    user5 = auth_manager.create_user(
        merchant_id=merchant2.merchant_id,
        username="bob.martin",
        email="bob.martin@shopifyplus.com",
        password="password123",
        full_name="Bob Martin",
        role="user"
    )
    print(f"   ✅ {user5.full_name} (@{user5.username}) - {user5.role}")
    print(f"      User ID: {user5.user_id}")
    print(f"      Login: bob.martin / password123")
    
    # Test Merchant 3: Financial Services
    print("\n📦 Creating Merchant 3: FinanceOne")
    merchant3 = auth_manager.create_merchant(
        merchant_name="financeone",
        company_name="FinanceOne Corporation",
        email="contact@financeone.com",
        phone="+1-555-0303"
    )
    print(f"✅ Merchant created: {merchant3.merchant_name}")
    print(f"   Merchant ID: {merchant3.merchant_id}")
    print(f"   API Key: {merchant3.api_key}")
    
    # Users for FinanceOne
    print("\n👤 Creating users for FinanceOne:")
    
    user6 = auth_manager.create_user(
        merchant_id=merchant3.merchant_id,
        username="emma.davis",
        email="emma.davis@financeone.com",
        password="password123",
        full_name="Emma Davis",
        role="admin"
    )
    print(f"   ✅ {user6.full_name} (@{user6.username}) - {user6.role}")
    print(f"      User ID: {user6.user_id}")
    print(f"      Login: emma.davis / password123")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 Test data created successfully!")
    print("\n📊 Summary:")
    print(f"   • 3 Merchants created")
    print(f"   • 6 Users created")
    print(f"   • All passwords: password123")
    
    print("\n🔐 Test Login Credentials:")
    print("\n   Merchant: TechCorp")
    print("   - john.doe / password123 (admin)")
    print("   - sarah.smith / password123 (user)")
    print("   - mike.johnson / password123 (user)")
    
    print("\n   Merchant: ShopifyPlus")
    print("   - alice.wong / password123 (admin)")
    print("   - bob.martin / password123 (user)")
    
    print("\n   Merchant: FinanceOne")
    print("   - emma.davis / password123 (admin)")
    
    print("\n" + "=" * 60)
    print("✅ Ready to test! Use these credentials to login.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    try:
        create_test_data()
    except Exception as e:
        print(f"\n❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
