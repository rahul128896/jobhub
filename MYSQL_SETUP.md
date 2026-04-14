# JobHub MySQL Database Setup Guide

## Prerequisites

You have MySQL installed on your system with:
- **User**: `root`
- **Password**: `Rahul@123`
- **Host**: `localhost`
- **Port**: `3306`

## Step 1: Verify MySQL is Running

### On Windows:
```bash
# Check if MySQL service is running
mysql -u root -p

# Enter password: Rahul@123
# If connected, you'll see: mysql>
# Type: exit
```

### On Linux/Mac:
```bash
# Start MySQL if not running
sudo service mysql start

# Test connection
mysql -u root -p
# Enter password: Rahul@123
```

## Step 2: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Key packages for MySQL:**
- `PyMySQL==1.1.0` - MySQL connector for Python
- `python-dotenv==1.2.1` - Load .env configuration
- `Flask==3.1.2` - Web framework

## Step 3: Configure Environment Variables

The `.env` file in the `backend/` directory is already configured with:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=Rahul@123
MYSQL_DATABASE=jobhub
```

**Note**: Never commit `.env` to Git with real passwords in production!

## Step 4: Initialize the Database

### Option A: Using Python Script (Recommended)

```bash
cd backend
python ../scripts/setup_mysql.py
```

This will:
1. ✅ Create the `jobhub` database
2. ✅ Create all required tables
3. ✅ Insert sample data
4. ✅ Display connection info

### Option B: Manual Setup

```bash
# Connect to MySQL
mysql -u root -p

# Enter password: Rahul@123

# Create database
CREATE DATABASE IF NOT EXISTS jobhub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Use database
USE jobhub;

# Exit
exit
```

Then run the Flask app which auto-initializes tables:
```bash
cd backend
python app.py
```

## Step 5: Start the Application

```bash
cd backend
python app.py
```

You should see:
```
[*] Initializing database...
[DB] Database 'jobhub' is ready.
[DB] All tables created / verified.
[DB] Sample users inserted.
[DB] Sample jobs inserted.
[DB] ✅ Database ready.
[*] Starting server on http://localhost:5000
```

## Database Schema

### Tables Created:

1. **users** - Job seekers, recruiters, admins
2. **jobs** - Job postings from recruiters
3. **applications** - Job applications from seekers
4. **saved_jobs** - Bookmarked jobs
5. **otp_attempts** - OTP verification tracking
6. **pending_registrations** - Pending user registrations

## Demo Accounts

After setup, use these credentials:

| Role | Email | Password |
|------|-------|----------|
| **Job Seeker** | rahul@example.com | password123 |
| **Recruiter** | recruiter@google.com | recruiter123 |
| **Admin** | admin@jobhub.com | admin123 |

## Verify Database Connection

### Check if Database Exists:
```bash
mysql -u root -p -e "SHOW DATABASES;" | grep jobhub
```

### View Tables:
```bash
mysql -u root -p jobhub -e "SHOW TABLES;"
```

### Count Records:
```bash
mysql -u root -p jobhub -e "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM jobs;"
```

## Troubleshooting

### Error: "Connection refused"
**Solution**: MySQL is not running
```bash
# Linux/Mac
sudo service mysql start

# Windows
net start MySQL80  # or your MySQL version
```

### Error: "Access denied for user 'root'"
**Solution**: Wrong password
- Check `.env` file
- Verify password with: `mysql -u root -p`

### Error: "Unknown database 'jobhub'"
**Solution**: Database not created
- Run: `python ../scripts/setup_mysql.py`
- Or: `mysql -u root -p < path/to/schema.sql`

### Error: "Table 'jobhub.users' doesn't exist"
**Solution**: Tables not created
- Start app with `python app.py` (auto-creates tables)
- Or run setup script again

## Environment Variables

Key variables in `.env`:

```env
# MySQL
MYSQL_HOST=localhost          # Database host
MYSQL_PORT=3306              # Default MySQL port
MYSQL_USER=root              # MySQL username
MYSQL_PASSWORD=Rahul@123     # Your MySQL password
MYSQL_DATABASE=jobhub        # Database name

# Flask
FLASK_ENV=development        # development/production
FLASK_DEBUG=True             # Enable debug mode
SECRET_KEY=...               # JWT secret key

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
```

## Next Steps

1. ✅ MySQL connected and running
2. ✅ Database initialized with sample data
3. **Run**: `python app.py`
4. **Visit**: http://localhost:5000
5. **Login**: Use demo account credentials above

## Database Backup

### Backup:
```bash
mysqldump -u root -p jobhub > jobhub_backup.sql
```

### Restore:
```bash
mysql -u root -p jobhub < jobhub_backup.sql
```

## Production Checklist

- [ ] Change MySQL password
- [ ] Use strong JWT_SECRET_KEY
- [ ] Set FLASK_ENV=production
- [ ] Use environment variables for credentials
- [ ] Enable SSL/TLS for MySQL connection
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Use connection pooling for high traffic

---

**For questions or issues**, check the backend logs or run setup script with verbose output.
