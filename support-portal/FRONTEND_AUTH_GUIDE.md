# 🎨 Frontend Authentication Setup - Complete!

## ✅ What's Been Added

1. **Login Page** (`/login`)
   - Clean, modern login UI
   - Test credentials displayed for easy access
   - Auto-fill credentials with one click
   - Stores auth token in localStorage

2. **User Profile Component**
   - Shows logged-in user info
   - Displays merchant/company name
   - Logout button
   - Appears in sidebar

3. **API Integration**
   - Automatically uses auth token when available
   - Falls back to X-User-Id for demo mode
   - All API calls now include authentication

---

## 🚀 How to Test (Step-by-Step)

### **Step 1: Set Up Test Data**

First, create test users in the backend:

```bash
cd c:\Users\fci\support_portal\support-portal\backend
python create_test_users.py
```

### **Step 2: Start Backend**

```bash
cd c:\Users\fci\support_portal\support-portal\backend
python app.py
```

Should show: `📍 Server: http://localhost:8000`

### **Step 3: Start Frontend**

```bash
cd c:\Users\fci\support_portal\support-portal\frontend
npm run dev
```

Should show: `- Local: http://localhost:3000`

### **Step 4: Open Browser and Login**

1. Go to: **http://localhost:3000/login**

2. You'll see the login page with test credentials listed:
   ```
   john.doe (TechCorp - admin)
   sarah.smith (TechCorp - user)
   alice.wong (ShopifyPlus - admin)
   bob.martin (ShopifyPlus - user)
   emma.davis (FinanceOne - admin)
   ```

3. **Click on any username** → It auto-fills the form!

4. Click **"Sign In"**

5. You'll be redirected to the dashboard with your user info showing in the sidebar

### **Step 5: Create a P1 Ticket**

1. Click **"P1 Critical"** in the sidebar

2. Fill out the form:
   - Subject: "Payment Gateway Down"
   - Description: "All transactions are failing"

3. Click **"Submit P1 Incident"**

4. **Check Slack!** The notification will show:
   ```
   Merchant: TechCorp
   User: John Doe
   Email: john.doe@techcorp.com
   ```

### **Step 6: Test Different Users**

1. Click **"Logout"** in the sidebar

2. Login as **alice.wong** (ShopifyPlus)

3. Create another P1 ticket

4. **Check Slack!** Now it shows:
   ```
   Merchant: ShopifyPlus
   User: Alice Wong
   Email: alice.wong@shopifyplus.com
   ```

---

## 🎯 What You'll See

### **Before Login:**
- Sidebar shows "Login" button
- API calls use demo user

### **After Login:**
- Sidebar shows:
  ```
  [Avatar] John Doe [admin]
           TechCorp Inc.
  [Logout]
  ```
- All tickets created with your merchant/user info
- Slack notifications include your details

---

## 🧪 Test Scenarios

### **Scenario 1: Same Merchant, Different Users**

```bash
1. Login as: john.doe (TechCorp)
2. Create P1 ticket
   → Slack shows: Merchant: TechCorp / User: John Doe

3. Logout

4. Login as: sarah.smith (TechCorp)
5. Create P1 ticket
   → Slack shows: Merchant: TechCorp / User: Sarah Smith

Result: Both tickets from same merchant, different users!
```

### **Scenario 2: Different Merchants**

```bash
1. Login as: john.doe (TechCorp)
2. Create P1 ticket
   → Slack shows: Merchant: TechCorp

3. Logout

4. Login as: alice.wong (ShopifyPlus)
5. Create P1 ticket
   → Slack shows: Merchant: ShopifyPlus

Result: Tickets tracked separately per merchant!
```

### **Scenario 3: User Creates Multiple Tickets**

```bash
1. Login as: john.doe
2. Create ticket: "Payment issue"
3. Create ticket: "Database error"
4. Go to "My Tickets"

Result: Both tickets show john.doe as creator
```

---

## 🎨 Frontend Features

### **Login Page** (`/login`)
- Auto-fill test credentials
- Error handling
- Loading states
- Option to continue in demo mode

### **User Profile Component** (Sidebar)
- Shows user avatar (initials)
- Full name + role badge
- Company name
- Logout button

### **Protected API Calls**
- All requests include `Authorization: Bearer <token>`
- Automatic fallback to demo mode
- Token stored securely in localStorage

---

## 📱 Quick Demo Flow

```
1. http://localhost:3000/login
   ↓ Click "john.doe"
   ↓ Click "Sign In"
   
2. Dashboard shows: "John Doe (admin) - TechCorp Inc."

3. Click "P1 Critical" → Create ticket

4. Check Slack → See merchant + user info!

5. Click "Logout" → Back to login page

6. Login as different user → Repeat!
```

---

## 🔐 Security Notes

- ✅ Tokens stored in localStorage (client-side only)
- ✅ Tokens expire after 7 days
- ✅ Logout clears token immediately
- ✅ API validates token on every request
- ✅ Merchant/user info tracked on every ticket

---

## 🆘 Troubleshooting

### "Login button not showing"
- Clear browser cache
- Check that UserProfile.tsx is imported in layout.tsx

### "Slack not showing merchant info"
- Make sure you're logged in (not demo mode)
- Check backend logs for authentication
- Verify ticket has merchant_name in database

### "Can't login"
- Run `python create_test_users.py` first
- Check backend is running: http://localhost:8000/health
- Check browser console for errors

---

## ✅ Complete Testing Checklist

- [ ] Backend running (http://localhost:8000)
- [ ] Frontend running (http://localhost:3000)
- [ ] Test users created (`python create_test_users.py`)
- [ ] Can login as john.doe
- [ ] User info shows in sidebar
- [ ] Can create P1 ticket
- [ ] Slack shows merchant + user info
- [ ] Can logout
- [ ] Can login as different user
- [ ] Different merchant shows in Slack
- [ ] Can continue in demo mode

---

## 🎉 You're All Set!

Everything is ready! Just:
1. Create test users
2. Start backend + frontend
3. Go to http://localhost:3000/login
4. Click any test credential
5. Sign in and create P1 tickets!

Slack will now show merchant and user information for every P1 incident! 🚀
