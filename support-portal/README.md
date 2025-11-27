# 🎉 Support Portal - Complete Working Setup

A full-stack support ticket system with Python FastAPI backend and Next.js frontend.

## 🚀 Quick Start Guide

### 1. Start Backend (API Server)
```cmd
cd support-portal\backend
run.bat
```
- Server will run at: **http://localhost:8000**
- API Documentation: **http://localhost:8000/docs**

### 2. Start Frontend (Next.js)
```cmd
cd support-portal\frontend  
copy example.env.local .env.local
npm install
npm run dev
```
- Frontend will run at: **http://localhost:3000**

### 3. Test the Complete Flow
1. **Home Dashboard** - View metrics and ticket counts
2. **Create Ticket** - Submit a new support ticket with file attachment
3. **My Tickets** - View all your submitted tickets  
4. **Ticket Details** - See ticket info and comments

## 📋 Project Structure

```
support-portal/
├── backend/                    # Python FastAPI API Server
│   ├── app.py                 # Main application (AWS Lambda ready)
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment configuration template
│   ├── run.bat               # Windows setup & run script
│   ├── test_api.py           # API testing script
│   └── README.md             # Backend documentation
│
└── frontend/                  # Next.js React Application
    ├── src/
    │   ├── app/              # Next.js App Router pages
    │   │   ├── page.tsx      # Home dashboard
    │   │   └── tickets/      # Ticket management pages
    │   ├── components/       # React components
    │   └── lib/
    │       ├── api.ts        # API client functions
    │       └── types.ts      # TypeScript types
    ├── package.json          # Node.js dependencies
    ├── example.env.local     # Environment template
    └── README.md             # Frontend documentation
```

## 🔧 Features Implemented

### ✅ Backend (Python FastAPI)
- **Create Ticket API** - Subject, priority, category, description, file attachment
- **Get My Tickets** - List all user tickets
- **Get Ticket Details** - Individual ticket information  
- **Get Comments** - Ticket comments and responses
- **Dashboard Metrics** - Total/Open/Resolved ticket counts
- **File Upload** - S3 upload with local storage fallback
- **SQLite Database** - Automatic schema creation and management
- **AWS Lambda Ready** - Structured for easy cloud deployment

### ✅ Frontend (Next.js)
- **Dashboard Home** - KPI cards showing ticket metrics
- **Create Ticket Form** - All fields including file upload
- **My Tickets Table** - List view with sorting and status
- **Ticket Detail View** - Full ticket info with comments
- **Error Handling** - User-friendly error messages
- **Responsive Design** - Works on desktop and mobile

### ✅ Integration
- **CORS Configured** - Backend accepts frontend requests
- **API Client** - Frontend makes HTTP requests to backend
- **File Upload** - Base64 encoding from frontend to backend
- **User Authentication** - Header-based user identification
- **Error Handling** - Consistent error responses

## 🗄️ Database Schema

**SQLite Database** (support_portal.db):

### tickets
- `id` (TEXT) - Primary key
- `subject` (TEXT) - Ticket title
- `priority` (TEXT) - low/medium/high
- `category` (TEXT) - User-defined category
- `description` (TEXT) - Ticket details
- `status` (TEXT) - open/in_progress/resolved/closed
- `user_id` (TEXT) - User identifier
- `created_at` (TEXT) - ISO timestamp
- `attachment_url` (TEXT) - File URL if attachment exists

### ticket_files
- `id` (TEXT) - Primary key
- `ticket_id` (TEXT) - Foreign key to tickets
- `file_url` (TEXT) - S3 or local file path
- `file_name` (TEXT) - Original filename
- `created_at` (TEXT) - Upload timestamp

### comments
- `id` (TEXT) - Primary key
- `ticket_id` (TEXT) - Foreign key to tickets
- `user_id` (TEXT) - Commenter identifier
- `comment` (TEXT) - Comment text
- `created_at` (TEXT) - Comment timestamp

## 🌐 API Endpoints

All endpoints support CORS and expect `X-User-Id` header:

- **GET** `/health` - Health check
- **POST** `/tickets` - Create ticket with file upload
- **GET** `/tickets/my` - Get user's tickets
- **GET** `/tickets/{id}` - Get specific ticket
- **GET** `/tickets/{id}/comments` - Get ticket comments
- **GET** `/dashboard/metrics` - Get dashboard statistics

## 📁 File Upload System

- **Frontend**: Converts files to Base64
- **Backend**: Decodes and stores files
- **S3 Storage**: If AWS credentials provided
- **Local Storage**: Fallback to `backend/uploads/` folder
- **Size Limit**: 10MB maximum file size

## 🔐 Authentication

**Development Mode** (Current):
- Uses `X-User-Id: demo-user` header
- No password required
- All users see their own tickets

**Production Ready**:
- Replace header auth with JWT tokens
- Add user registration/login
- Integrate with AWS Cognito or Auth0

## ⚙️ Configuration

### Backend Environment (.env)
```env
# Database (PostgreSQL fallback)
DATABASE_URL=postgresql://user:pass@host/db

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret  
S3_BUCKET_NAME=your-bucket

# Server settings
PORT=8000
DEBUG=true
DEFAULT_USER_ID=demo-user
```

### Frontend Environment (.env.local)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_DEFAULT_USER_ID=demo-user
```

## 🚀 AWS Deployment (Future)

The backend is designed for easy AWS Lambda deployment:

1. **Lambda Function**: `app.py` includes `lambda_handler()`
2. **API Gateway**: Route HTTP requests to Lambda
3. **RDS Database**: Replace SQLite with PostgreSQL
4. **S3 Storage**: File uploads to S3 bucket
5. **Environment Variables**: Configure via Lambda environment

## 🧪 Testing

### Backend API Testing
```bash
cd backend
python test_api.py
```

### Manual Testing
1. Start both backend and frontend
2. Open http://localhost:3000
3. Create a test ticket with file attachment
4. Verify it appears in "My Tickets"
5. Check dashboard metrics update

### API Documentation
- Interactive testing at: http://localhost:8000/docs
- Try all endpoints directly in browser

## 🔧 Development Workflow

1. **Backend Changes**: 
   - Edit `backend/app.py`
   - Server auto-reloads
   - Test at `/docs`

2. **Frontend Changes**:
   - Edit files in `frontend/src/`
   - Next.js auto-reloads
   - View at `localhost:3000`

3. **Database Changes**:
   - Tables created automatically
   - Delete `support_portal.db` to reset
   - Check data with SQLite browser

## 🐛 Troubleshooting

### Backend Won't Start
- Check Python version (3.8+ required)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 isn't in use

### Frontend Won't Connect
- Verify backend is running at localhost:8000
- Check `.env.local` has correct API URL
- Look for CORS errors in browser console

### File Upload Issues
- Check file size under 10MB
- Verify `backend/uploads/` folder exists
- For S3: check AWS credentials

### Database Issues
- SQLite file created automatically
- Check write permissions in backend folder
- For PostgreSQL: verify DATABASE_URL format

## 📊 Production Checklist

Before deploying to production:

- [ ] Replace SQLite with PostgreSQL/RDS
- [ ] Configure proper authentication (JWT/Cognito)
- [ ] Set up S3 bucket for file storage
- [ ] Add rate limiting and security headers
- [ ] Configure environment variables
- [ ] Set up monitoring and logging
- [ ] Add backup strategy for database
- [ ] Configure domain and SSL certificate

---

## 🎯 Summary

You now have a **complete, working support portal** with:
- ✅ Python FastAPI backend with all required endpoints
- ✅ Next.js frontend with dashboard, ticket creation, and management
- ✅ File upload system (local storage + S3 ready)
- ✅ SQLite database with automatic schema
- ✅ Full integration between frontend and backend
- ✅ AWS Lambda deployment ready code
- ✅ Comprehensive documentation and testing

**Ready for development, testing, and AWS deployment!** 🚀