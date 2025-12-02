# 🔐 Authentication & Multi-Merchant System

## Overview

The support portal now includes a complete authentication system with:
- **Merchants** (companies/organizations)
- **Users** (individuals within merchants)
- **Session-based authentication**
- **Merchant and user details in tickets and Slack notifications**

---

## 🚀 Quick Start

### 1. Create Test Data

Run this script to create 3 test merchants with 6 users:

```bash
cd c:\Users\fci\support_portal\support-portal\backend
python create_test_users.py
```

This creates:
- **TechCorp** (3 users: john.doe, sarah.smith, mike.johnson)
- **ShopifyPlus** (2 users: alice.wong, bob.martin)
- **FinanceOne** (1 user: emma.davis)

All passwords: `password123`

---

## 🔑 Test Login Credentials

### Merchant: TechCorp
```
Username: john.doe
Password: password123
Role: admin

Username: sarah.smith  
Password: password123
Role: user

Username: mike.johnson
Password: password123
Role: user
```

### Merchant: ShopifyPlus
```
Username: alice.wong
Password: password123
Role: admin

Username: bob.martin
Password: password123
Role: user
```

### Merchant: FinanceOne
```
Username: emma.davis
Password: password123
Role: admin
```

---

## 📡 API Endpoints

### Authentication

#### **Login**
```http
POST /auth/login
Content-Type: application/json

{
  "username": "john.doe",
  "password": "password123"
}
```

Response:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "token": "SESSION_TOKEN_HERE",
    "user": {
      "user_id": "user_abc123",
      "merchant_id": "merchant_xyz789",
      "username": "john.doe",
      "email": "john.doe@techcorp.com",
      "full_name": "John Doe",
      "role": "admin",
      "merchant_name": "techcorp",
      "company_name": "TechCorp Inc."
    }
  }
}
```

#### **Get Current User**
```http
GET /auth/me
Authorization: Bearer SESSION_TOKEN_HERE
```

#### **Create Merchant** (Admin only)
```http
POST /auth/merchants
Content-Type: application/json

{
  "merchant_name": "newcompany",
  "company_name": "New Company Inc.",
  "email": "admin@newcompany.com",
  "phone": "+1-555-9999"
}
```

#### **Create User**
```http
POST /auth/users
Content-Type: application/json

{
  "merchant_id": "merchant_xyz789",
  "username": "new.user",
  "email": "new.user@company.com",
  "password": "password123",
  "full_name": "New User",
  "role": "user"
}
```

---

## 🎫 Creating Tickets with Authentication

### Using Session Token (Recommended)

```http
POST /tickets
Authorization: Bearer SESSION_TOKEN_HERE
Content-Type: application/json

{
  "subject": "Payment Gateway Down",
  "priority": "P1",
  "category": "P1 Critical Incident",
  "description": "All payment transactions are failing"
}
```

The backend will automatically:
1. ✅ Extract user info from session token
2. ✅ Store merchant_id, merchant_name, user_name, user_email in ticket
3. ✅ Include this info in Slack notifications

### Using Legacy X-User-Id Header (Backwards Compatible)

```http
POST /tickets
X-User-Id: demo-user
Content-Type: application/json

{
  "subject": "Test Ticket",
  "priority": "medium",
  "category": "Technical Issue",
  "description": "Testing"
}
```

---

## 📊 Slack Notifications with Merchant/User Info

When a P1 ticket is created, Slack receives:

```
🚨 P1 CRITICAL INCIDENT ALERT

Incident ID: P1-20251201-ABC123
Priority: P1
Merchant: TechCorp
User: John Doe
Email: john.doe@techcorp.com
Created: 2025-12-01 15:30:00 UTC

Subject: Payment Gateway Down
Description: All payment transactions are failing...

🔥 IMMEDIATE ACTION REQUIRED | Ticket ID: `abc123`
```

---

## 🏗️ Database Schema

### Merchants Table
```sql
CREATE TABLE merchants (
    merchant_id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL UNIQUE,
    company_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    status TEXT DEFAULT 'active',
    api_key TEXT UNIQUE,
    created_at TEXT NOT NULL
);
```

### Users Table
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    last_login TEXT,
    FOREIGN KEY (merchant_id) REFERENCES merchants (merchant_id)
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL  -- 7 days from creation
);
```

### Updated Tickets Table
Now includes merchant/user columns:
```sql
ALTER TABLE tickets ADD COLUMN merchant_id TEXT;
ALTER TABLE tickets ADD COLUMN merchant_name TEXT;
ALTER TABLE tickets ADD COLUMN user_name TEXT;
ALTER TABLE tickets ADD COLUMN user_email TEXT;
```

---

## 🧪 Testing Workflow

### 1. Create Test Data
```bash
python create_test_users.py
```

### 2. Login as User
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe", "password": "password123"}'
```

Save the returned token.

### 3. Create P1 Ticket
```bash
curl -X POST http://localhost:8000/tickets \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Database Connection Lost",
    "priority": "P1",
    "category": "P1 Critical Incident",
    "description": "Cannot connect to production database"
  }'
```

### 4. Check Slack
The notification will include:
- Merchant: TechCorp
- User: John Doe
- Email: john.doe@techcorp.com

### 5. Create Another Ticket from Same Merchant
Login as sarah.smith and create another ticket. Slack will show:
- Merchant: TechCorp (same merchant)
- User: Sarah Smith (different user)
- Email: sarah.smith@techcorp.com

### 6. Create Ticket from Different Merchant
Login as alice.wong and create a ticket. Slack will show:
- Merchant: ShopifyPlus (different merchant)
- User: Alice Wong
- Email: alice.wong@shopifyplus.com

---

## 🔍 Querying Tickets by Merchant

### Get All Tickets for a Merchant
```sql
SELECT * FROM tickets WHERE merchant_id = 'merchant_xyz789';
```

### Get All Users for a Merchant
```sql
SELECT * FROM users WHERE merchant_id = 'merchant_xyz789';
```

### Get Ticket Count by Merchant
```sql
SELECT merchant_name, COUNT(*) as ticket_count 
FROM tickets 
GROUP BY merchant_name;
```

---

## 🎯 Use Cases

### 1. Same Merchant, Multiple Users
- **Merchant:** TechCorp
- **User 1:** john.doe creates ticket → Slack shows "TechCorp / John Doe"
- **User 2:** sarah.smith creates ticket → Slack shows "TechCorp / Sarah Smith"
- **Result:** Both tickets linked to same merchant, different users

### 2. Different Merchants
- **Merchant 1:** TechCorp → john.doe creates ticket
- **Merchant 2:** ShopifyPlus → alice.wong creates ticket
- **Result:** Tickets tracked separately per merchant

### 3. User Creates Multiple Tickets
- User: john.doe
- Ticket 1: "Payment issue" → Ticket ID: abc123
- Ticket 2: "Database error" → Ticket ID: def456
- **Result:** All tickets mapped to john.doe's user_id

---

## 🔐 Security Notes

- Passwords are hashed using SHA256
- Sessions expire after 7 days
- Each merchant has a unique API key for future API access
- User status can be set to 'inactive' to disable login

---

## 📈 Future Enhancements

- [ ] Password reset via email
- [ ] Two-factor authentication (2FA)
- [ ] Role-based permissions (admin vs user)
- [ ] API key authentication for programmatic access
- [ ] OAuth integration (Google, Microsoft, etc.)
- [ ] Audit logging for all user actions
- [ ] Merchant-level settings and customization

---

## 🆘 Troubleshooting

### "Invalid username or password"
- Check credentials are correct
- Verify user exists: `SELECT * FROM users WHERE username = 'john.doe';`
- Check user status: `SELECT status FROM users WHERE username = 'john.doe';`

### "Not authenticated"
- Include Authorization header: `Authorization: Bearer YOUR_TOKEN`
- Check token hasn't expired (7 days max)
- Re-login to get new token

### Merchant/user info not showing in Slack
- Verify you're using authenticated endpoints (with Bearer token)
- Check ticket has merchant_name and user_name columns populated
- Run: `SELECT merchant_name, user_name FROM tickets WHERE id = 'TICKET_ID';`

---

## ✅ Summary

You now have:
- ✅ **3 test merchants** with 6 test users
- ✅ **Authentication system** with login/logout
- ✅ **Session tokens** for secure API access
- ✅ **Merchant and user tracking** in all tickets
- ✅ **Slack notifications** showing merchant/user details
- ✅ **Multiple users per merchant** support
- ✅ **User-to-ticket mapping** for complete audit trail

Test it out! Login as different users and create P1 tickets to see merchant/user info in Slack! 🚀
