#!/usr/bin/env python3
"""
Simple startup script for the Support Portal Backend
This avoids import conflicts when using uvicorn directly
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Support Portal API")
    print("=" * 50)
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("💾 Database: support_portal.db")
    print("📁 Uploads: uploads/")
    print("🏠 File Storage: Local only")
    print("=" * 50)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )