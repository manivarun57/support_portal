#!/usr/bin/env python3
"""
Add test user Dheeraj to TechCorp merchant for email testing
"""

import sqlite3
import hashlib
import uuid
from datetime import datetime, timezone

def add_dheeraj_user():
    """Add dheeraj user to TechCorp merchant"""
    conn = sqlite3.connect('support_portal.db')
    cursor = conn.cursor()
    
    # Get TechCorp merchant ID
    cursor.execute("SELECT merchant_id, merchant_name, company_name FROM merchants WHERE merchant_name = 'techcorp'")
    merchant = cursor.fetchone()
    
    if not merchant:
        print("❌ TechCorp merchant not found")
        conn.close()
        return
    
    merchant_id, merchant_name, company_name = merchant
    print(f"✅ Found merchant: {company_name} ({merchant_id})")
    
    # Check if user already exists
    cursor.execute("SELECT user_id, email FROM users WHERE email = 'dheeraj.narayanam@payintelli.com'")
    existing = cursor.fetchone()
    
    if existing:
        print(f"⚠️  User already exists: {existing[0]}")
        print(f"   Email: {existing[1]}")
        
        # Update to ensure it's in TechCorp
        cursor.execute("""
            UPDATE users 
            SET merchant_id = ?, username = 'dheeraj', full_name = 'Dheeraj'
            WHERE email = 'dheeraj.narayanam@payintelli.com'
        """, (merchant_id,))
        conn.commit()
        print("✅ Updated user to TechCorp merchant")
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        username = "dheeraj"
        email = "dheeraj.narayanam@payintelli.com"
        full_name = "Dheeraj"
        
        # Hash password: "password123"
        password = "password123"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (
                user_id, merchant_id, username, email, password_hash,
                full_name, role, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            merchant_id,
            username,
            email,
            password_hash,
            full_name,
            'user',
            'active',
            datetime.now(timezone.utc).isoformat()
        ))
        
        conn.commit()
        print(f"\n✅ User created successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   Full Name: {full_name}")
        print(f"   Merchant: {company_name}")
    
    # Verify
    cursor.execute("""
        SELECT u.user_id, u.username, u.email, u.full_name, u.role, m.company_name
        FROM users u
        JOIN merchants m ON u.merchant_id = m.merchant_id
        WHERE u.email = 'dheeraj.narayanam@payintelli.com'
    """)
    
    result = cursor.fetchone()
    
    if result:
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        print(f"User ID: {result[0]}")
        print(f"Username: {result[1]}")
        print(f"Email: {result[2]}")
        print(f"Full Name: {result[3]}")
        print(f"Role: {result[4]}")
        print(f"Merchant: {result[5]}")
        print("=" * 70)
        
        print("\n📧 LOGIN CREDENTIALS:")
        print(f"   Email: {result[2]}")
        print(f"   Password: password123")
        
        print("\n🧪 TO TEST EMAIL NOTIFICATIONS:")
        print("1. Login with above credentials")
        print("2. Create a P1 Critical ticket")
        print("3. Check email: dheeraj.narayanam@payintelli.com")
        print("4. Email should arrive with subject: 'P1 critical has been made'")
    
    conn.close()

if __name__ == "__main__":
    add_dheeraj_user()
