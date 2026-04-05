#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run.py — Quick start script for JobHub Job Portal
Run: python run.py
Then open: http://localhost:5000
"""

import os
import sys

# Ensure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

from database import init_db
from app import app

if __name__ == '__main__':
    print("\n" + "="*55)
    print("  >> JobHub Job Portal - Starting Server")
    print("="*55)

    # Initialize database
    init_db()

    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    print(f"\n  [+] Server running at: http://localhost:{port}")
    print(f"  [+] Database:          jobhub.db")
    print(f"  [+] Uploads folder:    uploads/")
    print("\n  Demo Accounts:")
    print("  +---------------------------------------------+")
    print("  | Job Seeker:  rahul@example.com / password123 |")
    print("  | Recruiter:   recruiter@google.com / recruiter123 |")
    print("  +---------------------------------------------+")
    print("\n  Press Ctrl+C to stop\n")

    app.run(host='0.0.0.0', port=port, debug=debug)
