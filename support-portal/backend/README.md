# Support Portal Backend

A standalone Python backend built with FastAPI that provides all the APIs needed by the Next.js frontend.

## 🚀 Quick Start

### Windows (Recommended)
```cmd
# Run the setup and start script
run.bat
```

### Manual Setup
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file
copy .env.example .env

# 5. Run the server
python app.py
```

## 📋 API Endpoints

The backend provides these endpoints that match your frontend's expectations:

### Core Endpoints
- **GET** `/` - API information
- **GET** `/health` - Health check
- **GET** `/docs` - Interactive API documentation

### Ticket Management
- **POST** `/tickets` - Create a new ticket with optional file attachment
- **GET** `/tickets/my` - Get all tickets for the current user
- **GET** `/tickets/{ticket_id}` - Get specific ticket details
- **GET** `/tickets/{ticket_id}/comments` - Get comments for a ticket
- **GET** `/dashboard/metrics` - Get dashboard metrics (total, open, resolved tickets)

## 🗄️ Database

The backend uses **SQLite** by default (file: `support_portal.db`) with automatic fallback from PostgreSQL if configured.

### Database Schema
- **tickets** - Main ticket information
- **ticket_files** - File attachments linked to tickets  
- **comments** - Comments on tickets

## 📁 File Uploads

Supports file attachments with:
- **S3 Upload** - If AWS credentials are configured
- **Local Storage** - Fallback to `uploads/` folder
- **Base64 Support** - Frontend sends files as base64 data
- **File Size Limit** - 10MB by default

## 🔧 Configuration

Edit `.env` file to customize settings:

```env
# Database (leave empty to use SQLite)
DATABASE_URL=postgresql://user:pass@localhost/support_portal

# AWS S3 (leave empty to use local storage)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your-bucket-name

# Server settings
PORT=8000
DEBUG=true
DEFAULT_USER_ID=demo-user
```

## 🔐 Authentication

- Uses `X-User-Id` header for user identification
- Falls back to `DEFAULT_USER_ID` from environment
- Compatible with your frontend's authentication

## 🌐 CORS & Frontend Integration

- CORS is fully enabled for frontend integration
- Accepts requests from any origin during development
- Frontend should work without changes by pointing to `http://localhost:8000`

## 🧪 Testing

### Using the Interactive Documentation
1. Start the server: `run.bat`
2. Open: http://localhost:8000/docs
3. Try out endpoints directly in the browser

### Using curl
```bash
# Health check
curl http://localhost:8000/health

# Create a ticket
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -H "X-User-Id: demo-user" \
  -d '{
    "subject": "Test Issue",
    "priority": "medium", 
    "category": "general",
    "description": "This is a test ticket"
  }'

# Get my tickets
curl -H "X-User-Id: demo-user" http://localhost:8000/tickets/my

# Get dashboard metrics
curl -H "X-User-Id: demo-user" http://localhost:8000/dashboard/metrics
```

## 📊 Features

✅ **FastAPI Framework** - Modern, fast, and well-documented
✅ **SQLite Database** - No setup required, works out of the box
✅ **File Upload Support** - S3 or local storage
✅ **Interactive API Docs** - Built-in Swagger UI
✅ **Error Handling** - Comprehensive error responses
✅ **CORS Enabled** - Ready for frontend integration
✅ **AWS Lambda Ready** - Designed for easy AWS deployment
✅ **Environment Configuration** - Flexible setup via .env file

## 🚀 AWS Lambda Deployment (Future)

The code is structured to be AWS Lambda-ready:
- `lambda_handler()` function included for Lambda deployment
- Environment-based configuration
- Stateless design
- Compatible with AWS API Gateway

## 🐛 Troubleshooting

### Common Issues

**Port already in use:**
- Change `PORT=8000` in `.env` file

**Import errors:**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`

**Database errors:**
- Check file permissions in backend directory
- SQLite file will be created automatically

**File upload errors:**
- Check `uploads/` folder exists and is writable
- Verify file size is under 10MB limit

### Logs
The server logs all activity to the console. Watch for:
- Request details and timing
- Database operations
- File upload status
- Error details with stack traces

## 🔄 Development Workflow

1. **Start backend:** `run.bat` 
2. **Start frontend:** `npm run dev` (in frontend directory)
3. **Make changes:** Both will hot-reload automatically
4. **Test:** Use interactive docs or frontend
5. **Deploy:** Convert to Lambda when ready

The backend is designed to work seamlessly with your existing Next.js frontend while providing a solid foundation for AWS deployment.