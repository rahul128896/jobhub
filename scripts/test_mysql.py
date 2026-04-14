#!/usr/bin/env python3
"""
test_mysql.py
==============
Test MySQL connection and database setup

Usage:
    cd backend
    python ../scripts/test_mysql.py
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

import pymysql


def test_connection():
    """Test basic MySQL connection"""
    from database import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_PORT
    
    print("\n" + "=" * 60)
    print(" " * 15 + "🔍 MySQL Connection Test")
    print("=" * 60)
    
    print("\n[*] Configuration:")
    print(f"    Host:     {MYSQL_HOST}")
    print(f"    Port:     {MYSQL_PORT}")
    print(f"    User:     {MYSQL_USER}")
    
    print("\n[*] Testing connection...")
    
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
            charset='utf8mb4'
        )
        print("    ✅ Connection successful!")
        conn.close()
        
    except pymysql.MySQLError as e:
        print(f"    ❌ Connection failed: {e}")
        print("\n[!] Troubleshooting:")
        print("    1. Is MySQL running? (service mysql status)")
        print("    2. Is password correct? Check backend/.env")
        print("    3. Is user 'root' configured? (mysql -u root -p)")
        return False
    
    return True


def test_database():
    """Test database and tables"""
    from database import get_db, MYSQL_DATABASE
    
    print("\n[*] Checking database...")
    
    try:
        conn = get_db()
        
        # Check database
        print(f"    ✅ Database '{MYSQL_DATABASE}' accessible")
        
        # Check tables
        tables = conn.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s
        """, (MYSQL_DATABASE,)).fetchall()
        
        table_names = [t['TABLE_NAME'] for t in tables]
        print(f"    ✅ Found {len(table_names)} tables:")
        for name in sorted(table_names):
            print(f"       - {name}")
        
        # Count records
        print("\n[*] Data in tables:")
        
        users = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()['n']
        print(f"    ✅ Users: {users}")
        
        jobs = conn.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()['n']
        print(f"    ✅ Jobs: {jobs}")
        
        apps = conn.execute("SELECT COUNT(*) AS n FROM applications").fetchone()['n']
        print(f"    ✅ Applications: {apps}")
        
        saved = conn.execute("SELECT COUNT(*) AS n FROM saved_jobs").fetchone()['n']
        print(f"    ✅ Saved Jobs: {saved}")
        
        conn.close()
        
    except Exception as e:
        print(f"    ❌ Database error: {e}")
        return False
    
    return True


def test_demo_accounts():
    """Test demo account credentials"""
    from database import get_db
    import hashlib
    
    print("\n[*] Checking demo accounts...")
    
    try:
        conn = get_db()
        
        accounts = [
            ('rahul@example.com', 'password123', 'Job Seeker'),
            ('recruiter@google.com', 'recruiter123', 'Recruiter'),
            ('admin@jobhub.com', 'admin123', 'Admin'),
        ]
        
        for email, password, role in accounts:
            user = conn.execute(
                "SELECT id, name, role FROM users WHERE email = %s LIMIT 1",
                (email,)
            ).fetchone()
            
            if user:
                print(f"    ✅ {role}: {user['name']} ({email})")
            else:
                print(f"    ⚠️  {role}: Not found ({email})")
        
        conn.close()
        
    except Exception as e:
        print(f"    ❌ Error checking accounts: {e}")
        return False
    
    return True


def main():
    print("\n" + "=" * 60)
    print(" " * 12 + "🧪 JobHub MySQL Setup Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Connection
    if not test_connection():
        all_passed = False
    else:
        # Test 2: Database
        if not test_database():
            all_passed = False
        
        # Test 3: Demo accounts
        if not test_demo_accounts():
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print(" " * 20 + "✅ All tests passed!")
        print("\n[✓] You can now:")
        print("    1. Run: python backend/app.py")
        print("    2. Visit: http://localhost:5000")
        print("    3. Login with demo accounts above")
        print("\n" + "=" * 60 + "\n")
        return True
    else:
        print(" " * 15 + "❌ Some tests failed - see above")
        print("\n[!] Run setup first:")
        print("    python ../scripts/setup_mysql.py")
        print("\n" + "=" * 60 + "\n")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
