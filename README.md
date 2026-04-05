# JobHub — Full Stack Job Portal

**Tech Stack:** HTML · CSS · JavaScript · Python (Flask) · SQLite/MySQL · JWT Auth

---

## 📁 Project Structure

```
jobportal/
├── backend/
│   ├── app.py              ← Flask app — serves frontend + API
│   ├── run.py              ← Quick start script
│   ├── database.py         ← SQLite schema + seed data
│   ├── auth_utils.py       ← JWT tokens + password hashing
│   ├── requirements.txt
│   ├── .env                ← Environment variables
│   ├── routes/
│   │   ├── auth.py         ← /api/register /api/login /api/profile
│   │   ├── jobs.py         ← /api/jobs CRUD + search + filters
│   │   └── applications.py ← /api/apply + status + resume download
│   └── uploads/            ← Resume files (auto-created)
│
└── frontend/
    ├── index.html          ← Home page
    ├── login.html          ← Login
    ├── register.html       ← Register (role selection)
    ├── jobs.html           ← Job listings with filters
    ├── job-details.html    ← Full job info + apply button
    ├── apply.html          ← 3-step application form
    ├── dashboard.html      ← Role-based dashboard
    ├── css/                ← Stylesheets
    ├── js/
    │   ├── api.js          ← Centralized API client (AuthAPI, JobsAPI, ApplicationsAPI)
    │   ├── auth.js         ← Login / Register logic
    │   ├── jobs.js         ← Job listing + filtering
    │   ├── job-details.js  ← Job detail page
    │   ├── apply.js        ← Multi-step application form
    │   └── dashboard.js    ← Seeker & Recruiter dashboards
    └── components/
        ├── navbar.html
        └── footer.html
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install flask PyJWT python-dotenv Werkzeug
```

### 2. Run the server

```bash
cd backend
python run.py
```

### 3. Open in browser

```
http://localhost:5000
```

Flask serves both the frontend and the API from the same port — **no CORS issues**.

---

## 🔐 Demo Accounts

| Role        | Email                        | Password       |
|-------------|------------------------------|----------------|
| Job Seeker  | rahul@example.com            | password123    |
| Recruiter   | recruiter@google.com         | recruiter123   |

---

## 📡 API Endpoints

### Auth

| Method | Endpoint              | Auth     | Description              |
|--------|-----------------------|----------|--------------------------|
| POST   | `/api/register`       | Public   | Register new user        |
| POST   | `/api/login`          | Public   | Login, returns JWT token |
| GET    | `/api/me`             | Token    | Get current user profile |
| PUT    | `/api/profile`        | Token    | Update user profile      |
| PUT    | `/api/change-password`| Token    | Change password          |

### Jobs

| Method | Endpoint                      | Auth       | Description                    |
|--------|-------------------------------|------------|--------------------------------|
| GET    | `/api/jobs`                   | Optional   | List jobs (with filters)       |
| GET    | `/api/jobs/:id`               | Optional   | Get single job details         |
| POST   | `/api/jobs`                   | Recruiter  | Post a new job                 |
| PUT    | `/api/jobs/:id`               | Recruiter  | Update job (owner only)        |
| DELETE | `/api/jobs/:id`               | Recruiter  | Delete job (owner only)        |
| GET    | `/api/recruiter/jobs`         | Recruiter  | Get my posted jobs             |
| POST   | `/api/jobs/:id/save`          | Token      | Save/unsave a job              |
| GET    | `/api/saved-jobs`             | Token      | Get saved jobs list            |

### Applications

| Method | Endpoint                                    | Auth       | Description                    |
|--------|---------------------------------------------|------------|--------------------------------|
| POST   | `/api/apply`                                | Job Seeker | Apply for a job (+ resume)     |
| GET    | `/api/my-applications`                      | Job Seeker | My applications with status    |
| GET    | `/api/recruiter/applicants`                 | Recruiter  | All applicants for my jobs     |
| GET    | `/api/recruiter/jobs/:id/applications`      | Recruiter  | Applicants for a specific job  |
| PUT    | `/api/application/:id/status`               | Recruiter  | Update application status      |
| GET    | `/api/resume/:filename`                     | Token      | Download resume file           |

### Query Parameters for `/api/jobs`

```
?q=react           Search by title, company, or skills
?location=remote   Filter by location
?category=Engineering
?type=Full-time
?mode=Remote
?exp=1-3 years
?sort=latest|salary-high|salary-low
?page=1&per_page=20
```

---

## 🔑 Authentication Flow

```
1. User registers → POST /api/register → JWT token returned
2. User logs in   → POST /api/login   → JWT token returned
3. Token stored   → localStorage.setItem('token', token)
4. All protected routes → Authorization: Bearer <token>
5. Token expires  → 24 hours → redirect to login
```

---

## 🗄️ Database Schema

```sql
users        (id, name, email, password, role, phone, location, bio, linkedin, portfolio)
jobs         (id, recruiter_id, title, company, location, salary, job_type, category,
              experience, work_mode, description, responsibilities, requirements, skills, logo_url)
applications (id, job_id, seeker_id, name, email, phone, cover_letter, resume_filename,
              resume_path, status, applied_at)
saved_jobs   (id, user_id, job_id, saved_at)
```

---

## 🔄 Switching to MySQL (Production)

Replace `database.py` connection with:

```python
import pymysql
conn = pymysql.connect(
    host='localhost', user='root',
    password='yourpass', database='jobhub',
    cursorclass=pymysql.cursors.DictCursor
)
```

Replace `?` placeholders with `%s` in all SQL queries.

---

## 📦 Environment Variables (.env)

```env
SECRET_KEY=your_flask_secret
JWT_SECRET_KEY=your_jwt_secret
DATABASE_PATH=jobhub.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=5242880
FLASK_DEBUG=True
PORT=5000
```

---

## ✨ Features

- ✅ Role-based authentication (Job Seeker / Recruiter)
- ✅ JWT token auth with 24hr expiry
- ✅ Job listing with search + 5 filters + sort
- ✅ 3-step application form with resume upload
- ✅ Application status tracking (Under Review / Shortlisted / Hired / Rejected)
- ✅ Recruiter: post/edit/delete jobs, view applicants, update status
- ✅ Job Seeker: browse jobs, save jobs, track applications
- ✅ Responsive UI (mobile + desktop)
- ✅ Demo fallback — works without backend (mock data)
