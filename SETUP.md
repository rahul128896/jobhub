# JobHub - Complete Setup Guide

A modern, impressive job portal with MySQL database integration, beautiful UI, and full-featured job management system.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+ (already installed on your system)
- Node.js (optional, for frontend asset management)

### 1️⃣ Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2️⃣ Initialize MySQL Database

```bash
# From project root
python scripts/setup_mysql.py
```

This will:
- ✅ Create `jobhub` database
- ✅ Create all required tables
- ✅ Insert sample data
- ✅ Display demo account credentials

### 3️⃣ Start Backend Server

```bash
cd backend
python app.py
```

You should see:
```
============================================================
  JobHub API Server
============================================================
[*] Starting server on http://localhost:5000
```

### 4️⃣ Open in Browser

Visit: **http://localhost:5000**

---

## 📋 Configuration

### Environment Variables (.env)

Located in `backend/.env`:

```env
# MySQL Connection
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=Rahul@123
MYSQL_DATABASE=jobhub

# Flask Settings
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=jobhub_dev_secret_key_change_in_production
JWT_SECRET_KEY=jobhub_jwt_secret_key_change_in_production

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SENDER_NAME=JobHub
```

**For email:** Use Gmail App Password (not your regular password)
- Go to: https://myaccount.google.com/apppasswords
- Generate an app password for "Mail"
- Paste it in SENDER_PASSWORD

---

## 🔐 Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| **Job Seeker** | rahul@example.com | password123 |
| **Recruiter** | recruiter@google.com | recruiter123 |
| **Admin** | admin@jobhub.com | admin123 |

---

## 📁 Project Structure

```
jobhub/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── database.py            # MySQL connection & schema
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Configuration (created during setup)
│   ├── extensions.py           # Flask extensions (Mail, etc)
│   ├── routes/
│   │   ├── auth.py             # Login, register, OTP
│   │   ├── jobs.py             # Job listings
│   │   ├── applications.py      # Job applications
│   │   ├── admin.py            # Admin dashboard
│   │   ├── chat.py             # Chat functionality
│   │   └── ai.py               # AI features (resume analysis)
│   └── services/
│       ├── chatbot.py          # AI chatbot
│       └── resume_analyzer.py   # Resume analysis
│
├── frontend/
│   ├── index.html              # Home page
│   ├── jobs.html               # Job listings
│   ├── apply.html              # Application form
│   ├── dashboard.html          # User dashboard
│   ├── css/
│   │   ├── style.css           # Global styles
│   │   ├── home.css            # Home page styles
│   │   └── jobs.css            # Jobs page styles
│   └── js/
│       ├── api.js              # API client
│       ├── auth.js             # Authentication
│       ├── jobs.js             # Jobs functionality
│       └── apply.js            # Application handling
│
├── scripts/
│   ├── setup_mysql.py          # Database initialization
│   └── test_mysql.py           # Database verification
│
├── MYSQL_SETUP.md              # Detailed MySQL setup
└── SETUP.md                    # This file
```

---

## 🛠️ Database Schema

### Tables

**users** - User accounts
```
- id (PK)
- name, email, password
- role (jobseeker|recruiter|admin)
- phone, location, bio
- linkedin, portfolio, avatar
- two_factor_enabled
- created_at
```

**jobs** - Job postings
```
- id (PK)
- recruiter_id (FK: users)
- title, company, location, salary
- job_type, category, experience, work_mode
- description, responsibilities, requirements, skills
- logo_url
- is_active, views
- created_at
```

**applications** - Job applications
```
- id (PK)
- job_id (FK: jobs)
- seeker_id (FK: users)
- name, email, phone, linkedin, portfolio
- resume_filename, resume_path
- status (Under Review|Shortlisted|Hired|Rejected)
- applied_at
```

**saved_jobs** - Bookmarked jobs
```
- id (PK)
- user_id (FK: users)
- job_id (FK: jobs)
- saved_at
```

---

## ✅ Verification Steps

### 1. Test MySQL Connection

```bash
cd backend
python ../scripts/test_mysql.py
```

Should show:
```
✅ Connection successful!
✅ Database 'jobhub' accessible
✅ Found X tables
✅ Users: X
✅ Jobs: X
```

### 2. Check Database Directly

```bash
mysql -u root -p jobhub
# Enter password: Rahul@123

# View tables
SHOW TABLES;

# Count users
SELECT COUNT(*) FROM users;

# List demo accounts
SELECT email, role FROM users;

exit
```

### 3. Test API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Should return:
# {"status":"ok","message":"JobHub API is running",...}
```

---

## 🎨 Modern UI Features

The redesigned interface includes:

- **Premium Color Scheme**: Indigo (#6366F1) primary + Hot Pink (#EC4899) accent
- **Glassmorphism Effects**: Frosted glass cards with backdrop blur
- **Gradient Accents**: Linear gradients on buttons and elements
- **Bold Typography**: 900 weight headers for visual impact
- **Smooth Animations**: Enhanced hover effects and transitions
- **Shadow Depth**: Layered shadows for 3D appearance
- **Responsive Design**: Mobile-first approach
- **Dark Mode**: Premium dark theme throughout

---

## 🔄 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/verify-otp` - OTP verification

### Jobs
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/<id>` - Get job details
- `POST /api/jobs` - Create job (recruiters only)
- `PUT /api/jobs/<id>` - Update job
- `DELETE /api/jobs/<id>` - Delete job

### Applications
- `POST /api/applications` - Apply for job
- `GET /api/applications` - Get user's applications
- `PUT /api/applications/<id>` - Update application status

### Users
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update profile
- `POST /api/users/avatar` - Upload avatar

### Admin
- `GET /api/admin/statistics` - Platform statistics
- `GET /api/admin/users` - List all users
- `GET /api/admin/jobs` - Manage jobs

---

## 🐛 Troubleshooting

### MySQL Connection Error

**Error**: `[DB] ❌ MySQL connection failed`

**Solutions**:
1. Check MySQL is running:
   ```bash
   mysql -u root -p
   # Enter: Rahul@123
   ```

2. Verify .env credentials:
   ```bash
   cat backend/.env | grep MYSQL
   ```

3. Test connection:
   ```bash
   python scripts/test_mysql.py
   ```

### Database Not Found

**Error**: `Unknown database 'jobhub'`

**Solution**: Run setup script:
```bash
python scripts/setup_mysql.py
```

### Tables Not Found

**Error**: `Table 'jobhub.users' doesn't exist`

**Solution**: Start app (auto-creates tables):
```bash
cd backend
python app.py
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**: Change port in .env:
```env
PORT=5001
```

Then access: http://localhost:5001

### Email Verification Issues

**Error**: `SMTP authentication failed`

**Solutions**:
1. Use Gmail App Password (not regular password)
2. Enable "Less secure app access" if not using app password
3. Check SENDER_EMAIL is correct
4. Verify SMTP_SERVER and SMTP_PORT

---

## 📚 Additional Resources

- [MySQL Setup Guide](./MYSQL_SETUP.md) - Detailed MySQL configuration
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyMySQL Documentation](https://pymysql.readthedocs.io/)
- [JWT Authentication](https://jwt.io/)

---

## 🚀 Deployment

### Before Production:

1. **Security**:
   ```env
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=your_secure_random_key_here
   JWT_SECRET_KEY=your_secure_jwt_key_here
   ```

2. **Database**:
   - Change MySQL password
   - Enable SSL/TLS
   - Set up automated backups
   - Configure firewall rules

3. **Performance**:
   - Enable connection pooling
   - Set up caching layer (Redis)
   - Configure CDN for static assets
   - Use WSGI server (Gunicorn, uWSGI)

### Deploy with Gunicorn:

```bash
pip install gunicorn

# Run
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📞 Support

For issues or questions:
1. Check error messages in console
2. Run verification scripts
3. Review log files
4. Check database directly with MySQL CLI

---

**Last Updated**: 2024
**Version**: 1.0.0
**License**: MIT
