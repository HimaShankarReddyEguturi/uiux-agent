#!/usr/bin/env python3
"""
Startup script for PDF to JSON conversion API with CORS support
"""

import uvicorn
import os
import sys
from pathlib import Path

def main():
    """Start the FastAPI server with proper CORS configuration"""
    
    # Add the app directory to Python path
    app_dir = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_dir))
    
    print("Starting PDF to JSON API Server")
    print("=" * 40)
    print("Working directory:", os.getcwd())
    print("Server will be available at: http://localhost:8000")
    print("API endpoints:")
    print("   - POST /upload - Upload PDF/DOCX for conversion")
    print("   - GET  /latest-report - Get latest conversion result")
    print("   - GET  /health - Health check")
    print("   - GET  /upload-and-report - Upload form")
    print("CORS enabled for Figma plugin integration")
    print("=" * 40)
    
    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    main()