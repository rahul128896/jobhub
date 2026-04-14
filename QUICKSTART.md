# 🚀 JobHub - Quick Start (5 Minutes)

## Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Initialize MySQL
```bash
python ../scripts/setup_mysql.py
```

Wait for completion ✅

## Step 3: Start Server
```bash
python app.py
```

## Step 4: Open Browser
Visit: **http://localhost:5000**

---

## 🔐 Login Credentials

**Job Seeker:**
- Email: `rahul@example.com`
- Password: `password123`

**Recruiter:**
- Email: `recruiter@google.com`
- Password: `recruiter123`

**Admin:**
- Email: `admin@jobhub.com`
- Password: `admin123`

---

## 📊 What's Included

✅ **Beautiful Modern UI** - Premium design with glassmorphism
✅ **MySQL Database** - Full user management system
✅ **Job Listings** - Browse, search, and apply for jobs
✅ **User Dashboard** - Track applications and saved jobs
✅ **Recruiter Portal** - Post jobs and review applications
✅ **Admin Panel** - Manage users and platform
✅ **Authentication** - Secure login with JWT
✅ **OTP Verification** - Email-based verification
✅ **Resume Upload** - File upload support
✅ **Chat System** - Built-in messaging
✅ **AI Features** - Resume analysis and recommendations

---

## ⚠️ If Something Goes Wrong

### MySQL Not Running?
```bash
# Linux/Mac
sudo service mysql start

# Windows
net start MySQL80
```

### Test Connection?
```bash
python ../scripts/test_mysql.py
```

### Need More Help?
See [SETUP.md](./SETUP.md) for detailed instructions

---

**Enjoy! 🎉**
