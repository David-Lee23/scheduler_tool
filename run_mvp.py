#!/usr/bin/env python3
"""
Simple MVP Startup Script
"""

import subprocess
import sys
import os

def main():
    print("🚛 Trucking Schedule MVP")
    print("=" * 40)
    
    # Check if database exists
    if os.path.exists('trucking_schedule.db'):
        print("✅ Database found")
    else:
        print("⚠️  No database found - upload a PDF to get started")
    
    print("🌐 Starting server at http://localhost:5000")
    print("📤 Upload PDFs at http://localhost:5000/upload")
    print("🗂️  Manage trips at http://localhost:5000/trips")
    print("-" * 40)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == '__main__':
    main() 