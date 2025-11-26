#!/usr/bin/env python3
"""
Minimal test server to debug the shutdown issue
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create minimal app
app = FastAPI(title="Test API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Test API is working"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("🧪 Starting Test API Server...")
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )