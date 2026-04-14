#!/usr/bin/env python3
"""
setup_mysql.py
==============
Initialize JobHub MySQL Database

Usage:
    cd backend
    python ../scripts/setup_mysql.py

This script will:
1. Create the 'jobhub' database if it doesn't exist
2. Create all required tables (users, jobs, applications, etc.)
3. Insert sample data for testing
4. Display connection info and test accounts
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

from database import init_db, get_db, MYSQL_HOST, MYSQL_USER, MYSQL_DATABASE, MYSQL_PORT


def main():
    print("\n" + "=" * 70)
    print(" " * 15 + "🚀 JobHub MySQL Database Setup")
    print("=" * 70)
    
    print("\n[✓] Configuration:")
    print(f"    Host:     {MYSQL_HOST}")
    print(f"    Port:     {MYSQL_PORT}")
    print(f"    User:     {MYSQL_USER}")
    print(f"    Database: {MYSQL_DATABASE}")
    
    print("\n[*] Initializing database...")
    try:
        init_db()
        print("\n[✅] Database setup completed successfully!")
        
        # Verify connection
        conn = get_db()
        user_count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()['n']
        job_count = conn.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()['n']
        conn.close()
        
        print("\n[✓] Database Status:")
        print(f"    Users in database:  {user_count}")
        print(f"    Jobs in database:   {job_count}")
        
    except Exception as e:
        print(f"\n[❌] Error: {e}")
        print("\n[!] Troubleshooting:")
        print("    1. Make sure MySQL is running: sudo service mysql start")
        print("    2. Check your credentials in backend/.env")
        print("    3. Ensure 'root' user has correct password")
        return False
    
    print("\n" + "=" * 70)
    print(" " * 15 + "✨ Demo Account Credentials")
    print("=" * 70)
    print("\n Job Seeker (Applicant):")
    print("    Email:    rahul@example.com")
    print("    Password: password123")
    print("\n Recruiter (Post Jobs & View Applications):")
    print("    Email:    recruiter@google.com")
    print("    Password: recruiter123")
    print("\n Admin (Manage Platform):")
    print("    Email:    admin@jobhub.com")
    print("    Password: admin123")
    
    print("\n" + "=" * 70)
    print(" " * 10 + "Start Backend Server: python backend/app.py")
    print("=" * 70 + "\n")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
