#!/usr/bin/env python3
"""
Startup script for the Wine Management API
"""

import uvicorn

if __name__ == "__main__":
    print("🍷 Starting Wine Management API...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔍 Interactive API explorer at: http://localhost:8000/redoc")
    print("🌐 API base URL: http://localhost:8000")
    print("\nPress Ctrl+C to stop the server")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Temporarily disable auto-reload
        log_level="info"
    )
