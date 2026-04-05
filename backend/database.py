"""
database.py
===========
MySQL database connection and schema setup for JobHub.

Uses PyMySQL with DictCursor so every row is accessed like a dict:
    row['column_name']

The MysqlConnection wrapper makes conn.execute() and conn.fetchone()
work the same way SQLite did, so route code stays clean.
"""

import os
import hashlib
import pymysql
import pymysql.cursors

# ── Credentials from .env ──────────────────────────────────────────────
MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'jobhub')
MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))

# Alias kept so nothing that imports DB_PATH breaks
DB_PATH = MYSQL_DATABASE


# ── Compatibility wrapper ──────────────────────────────────────────────
class MysqlConnection:
    """
    Thin wrapper around a PyMySQL connection that gives it a
    SQLite-like interface:

        conn = get_db()
        conn.execute("SELECT * FROM users WHERE id = %s", (1,))
        row  = conn.fetchone()
        rows = conn.fetchall()
        conn.commit()
        conn.close()

    Also exposes cursor.lastrowid via conn.lastrowid after an INSERT.
    """

    def __init__(self, raw_conn):
        self._conn   = raw_conn
        self._cursor = raw_conn.cursor()
        self.lastrowid = None

    # ── query helpers ──────────────────────────────────────────────────
    def execute(self, sql, params=None):
        """Run a SQL statement and return self (chainable)."""
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        self.lastrowid = self._cursor.lastrowid
        return self                 # allows .fetchone() chaining

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    # ── transaction helpers ────────────────────────────────────────────
    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._cursor.close()
        self._conn.close()


# ── GET CONNECTION ─────────────────────────────────────────────────────
def get_db() -> MysqlConnection:
    """
    Open a MySQL connection and return it wrapped in MysqlConnection.

    Usage in routes:
        conn = get_db()
        try:
            row = conn.execute("SELECT * FROM users WHERE id = %s", (uid,)).fetchone()
            ...
            conn.commit()
        finally:
            conn.close()
    """
    try:
        raw = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            connect_timeout=10,
        )
        return MysqlConnection(raw)

    except pymysql.MySQLError as e:
        print(f"[DB] ❌ MySQL connection failed: {e}")
        print("[DB] → Make sure MySQL is running and .env credentials are correct.")
        raise


# ── INITIALIZE DB ─────────────────────────────────────────────────────
def init_db():
    """
    Called once at server startup:
      1. Creates the 'jobhub' database if it doesn't exist.
      2. Creates all tables.
      3. Runs migrations (adds missing columns to existing installs).
      4. Seeds sample data on first run.
    """
    print("[DB] Initializing MySQL database...")
    _create_database_if_missing()

    conn = get_db()
    try:
        _create_tables(conn)
        conn.commit()
        _migrate(conn)
        _seed_data(conn)
    finally:
        conn.close()

    print("[DB] ✅ Database ready.")


# ── PRIVATE: CREATE DATABASE ──────────────────────────────────────────
def _create_database_if_missing():
    """Connect without specifying a DB and CREATE if not exists."""
    try:
        raw = pymysql.connect(
            host=MYSQL_HOST, user=MYSQL_USER,
            password=MYSQL_PASSWORD, port=MYSQL_PORT, charset='utf8mb4'
        )
        cur = raw.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        raw.commit()
        raw.close()
        print(f"[DB] Database '{MYSQL_DATABASE}' is ready.")
    except pymysql.MySQLError as e:
        print(f"[DB] ❌ Could not create database: {e}")
        raise


# ── PRIVATE: CREATE TABLES ────────────────────────────────────────────
def _create_tables(conn: MysqlConnection):
    """Create all tables. IF NOT EXISTS makes this safe to re-run."""

    # users
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id                 INT AUTO_INCREMENT PRIMARY KEY,
            name               VARCHAR(255)  NOT NULL,
            email              VARCHAR(255)  NOT NULL UNIQUE,
            password           VARCHAR(255)  NOT NULL,
            role               ENUM('jobseeker','recruiter','admin') NOT NULL,
            phone              VARCHAR(20),
            location           VARCHAR(255),
            bio                TEXT,
            linkedin           VARCHAR(255),
            portfolio          VARCHAR(255),
            avatar             VARCHAR(255),
            two_factor_enabled TINYINT(1)   NOT NULL DEFAULT 0,
            created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # jobs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            recruiter_id     INT          NOT NULL,
            title            VARCHAR(255) NOT NULL,
            company          VARCHAR(255) NOT NULL,
            location         VARCHAR(255) NOT NULL,
            salary           VARCHAR(100),
            job_type         VARCHAR(50)  NOT NULL DEFAULT 'Full-time',
            category         VARCHAR(100) NOT NULL DEFAULT 'Engineering',
            experience       VARCHAR(50)  NOT NULL DEFAULT '1-3 years',
            work_mode        VARCHAR(50)  NOT NULL DEFAULT 'On-site',
            description      LONGTEXT,
            responsibilities LONGTEXT,
            requirements     LONGTEXT,
            skills           LONGTEXT,
            logo_url         VARCHAR(500),
            is_active        TINYINT(1)  NOT NULL DEFAULT 1,
            views            INT         NOT NULL DEFAULT 0,
            created_at       TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recruiter_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # applications
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            job_id          INT          NOT NULL,
            seeker_id       INT          NOT NULL,
            name            VARCHAR(255) NOT NULL,
            email           VARCHAR(255) NOT NULL,
            phone           VARCHAR(20),
            linkedin        VARCHAR(255),
            portfolio       VARCHAR(255),
            experience      TEXT,
            cover_letter    TEXT,
            resume_filename VARCHAR(255),
            resume_path     VARCHAR(500),
            status          ENUM('Under Review','Shortlisted','Hired','Rejected')
                            NOT NULL DEFAULT 'Under Review',
            applied_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_application (job_id, seeker_id),
            FOREIGN KEY (job_id)    REFERENCES jobs(id)  ON DELETE CASCADE,
            FOREIGN KEY (seeker_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # saved_jobs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            user_id  INT       NOT NULL,
            job_id   INT       NOT NULL,
            saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_save (user_id, job_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id)  REFERENCES jobs(id)  ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # otp_attempts (includes attempt_count from day 1)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS otp_attempts (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            user_id       INT         NOT NULL,
            email         VARCHAR(255) NOT NULL,
            otp           VARCHAR(10)  NOT NULL,
            expires_at    DATETIME     NOT NULL,
            attempt_count TINYINT      NOT NULL DEFAULT 0,
            created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # pending_registrations (for 2-step registration with OTP)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_registrations (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            name      VARCHAR(255)  NOT NULL,
            email     VARCHAR(255)  NOT NULL UNIQUE,
            password  VARCHAR(255)  NOT NULL,
            role      ENUM('jobseeker','recruiter') NOT NULL,
            otp       VARCHAR(10)   NOT NULL,
            created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    print("[DB] All tables created / verified.")


# ── PRIVATE: MIGRATIONS ───────────────────────────────────────────────
def _migrate(conn: MysqlConnection):
    """Add missing columns to existing databases (safe to re-run)."""
    migrations = [
        ("users",        "two_factor_enabled",
         "ALTER TABLE users ADD COLUMN two_factor_enabled TINYINT(1) NOT NULL DEFAULT 0"),
        ("otp_attempts", "attempt_count",
         "ALTER TABLE otp_attempts ADD COLUMN attempt_count TINYINT NOT NULL DEFAULT 0"),
    ]
    for table, column, sql in migrations:
        try:
            exists = conn.execute("""
                SELECT COUNT(*) AS n
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """, (MYSQL_DATABASE, table, column)).fetchone()['n']
            if exists == 0:
                conn.execute(sql)
                conn.commit()
                print(f"[DB] Migration: added '{column}' to {table}")
        except Exception as e:
            print(f"[DB] Migration warning ({table}.{column}): {e}")


# ── PRIVATE: SEED DATA ─────────────────────────────────────────────────
def _seed_data(conn: MysqlConnection):
    """Insert demo users and jobs only if the tables are empty."""

    user_count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()['n']
    job_count  = conn.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()['n']

    if user_count > 0 and job_count > 0:
        print("[DB] Database already seeded — skipping.")
        return

    def _hash(pw):
        return hashlib.sha256(pw.encode()).hexdigest()

    # ── Demo users ─────────────────────────────────────────────────────
    if user_count == 0:
        users = [
            ('Rahul Sharma',     'rahul@example.com',    _hash('password123'), 'jobseeker',
             '+91 98765 43210',  'Delhi',     'Frontend developer with 2 years experience',
             'linkedin.com/in/rahul', 'github.com/rahul', None),
            ('Priya Patel',      'priya@example.com',    _hash('password123'), 'jobseeker',
             '+91 87654 32109',  'Mumbai',    'UI/UX designer with eye for detail',
             'linkedin.com/in/priya', 'github.com/priya', None),
            ('TechCorp HR',      'hr@techcorp.com',      _hash('recruiter123'), 'recruiter',
             '+91 11122 33344',  'Bangalore', 'Hiring top talent for TechCorp',
             'linkedin.com/company/techcorp', 'techcorp.com', None),
            ('Google Recruiter', 'recruiter@google.com', _hash('recruiter123'), 'recruiter',
             '+91 99988 77766',  'Remote',    'Google India Recruitment Team',
             'linkedin.com/company/google', 'google.com', None),
            ('Admin',            'admin@jobhub.com',     _hash('admin123'), 'admin',
             '+91 00000 00000',  'HQ',        'Platform Administrator', None, None, None),
        ]
        try:
            # PyMySQL doesn't have executemany on the wrapper, use raw cursor
            raw = conn._conn
            cur = raw.cursor()
            cur.executemany("""
                INSERT IGNORE INTO users
                    (name, email, password, role, phone, location, bio, linkedin, portfolio, avatar)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, users)
            raw.commit()
            print("[DB] Sample users inserted.")
        except Exception as e:
            print(f"[DB] Error inserting users: {e}")

    # Get recruiter IDs so we can assign jobs to them
    rows = conn.execute(
        "SELECT id FROM users WHERE role = 'recruiter' LIMIT 2"
    ).fetchall()
    rec_ids = [r['id'] for r in rows]
    r1 = rec_ids[0] if len(rec_ids) > 0 else 3
    r2 = rec_ids[1] if len(rec_ids) > 1 else 4

    # ── Demo jobs ──────────────────────────────────────────────────────
    if job_count == 0:
        jobs = [
            (r2, 'Senior Frontend Developer', 'Google', 'Remote', '₹12-18 LPA',
             'Full-time', 'Engineering', '3-5 years', 'Remote',
             'We are looking for a talented Senior Frontend Developer to build amazing web experiences.',
             '["Build responsive UIs with React","Optimize performance","Write clean code","Lead technical discussions"]',
             '["3+ years React experience","TypeScript proficiency","CSS/HTML expertise","REST API knowledge"]',
             '["React","TypeScript","CSS","JavaScript","Redux","WebPack"]',
             'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg', 1, 245),
            (r1, 'Backend Developer - Python', 'TechCorp', 'Bangalore', '₹15-20 LPA',
             'Full-time', 'Engineering', '3-5 years', 'Hybrid',
             'Join our backend team to build scalable microservices and REST APIs.',
             '["Design REST APIs","Build microservices","Write unit tests","Database optimization"]',
             '["3+ years Python/Node.js","MySQL/MongoDB experience","Docker knowledge","AWS basics"]',
             '["Python","Flask","MySQL","Docker","REST APIs","PostgreSQL"]',
             'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg', 1, 180),
            (r2, 'UI/UX Designer', 'Google', 'Delhi', '₹8-12 LPA',
             'Full-time', 'Design', '2-4 years', 'On-site',
             'Design beautiful and intuitive user experiences for our suite of products.',
             '["Create wireframes and prototypes","Conduct user research","Maintain design systems"]',
             '["2+ years UI/UX experience","Figma expert","Strong portfolio","Accessibility knowledge"]',
             '["Figma","Adobe XD","Prototyping","User Research","Design Systems","Sketch"]',
             'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg', 1, 310),
            (r1, 'Data Scientist', 'TechCorp', 'Mumbai', '₹18-25 LPA',
             'Full-time', 'Data Science', '3-5 years', 'Hybrid',
             'Work on cutting-edge ML models and data pipelines that drive business insights.',
             '["Build ML models","Analyze large datasets","Run A/B tests","Deploy models"]',
             '["3+ years data science","Python with Pandas/Scikit-learn","SQL proficiency","ML frameworks"]',
             '["Python","Machine Learning","TensorFlow","SQL","Statistics","Tableau"]',
             'https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg', 1, 270),
            (r2, 'DevOps Engineer', 'Google', 'Remote', '₹16-22 LPA',
             'Full-time', 'Engineering', '4-6 years', 'Remote',
             'Manage cloud infrastructure and CI/CD pipelines for our global application fleet.',
             '["Maintain CI/CD pipelines","Manage Kubernetes clusters","Monitor systems","Security"]',
             '["4+ years DevOps/SRE","Docker/Kubernetes expertise","AWS/GCP","Terraform experience"]',
             '["Docker","Kubernetes","AWS","Terraform","CI/CD","Linux"]',
             'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg', 1, 190),
            (r1, 'Junior Android Developer', 'TechCorp', 'Hyderabad', '₹6-10 LPA',
             'Full-time', 'Engineering', '1-2 years', 'On-site',
             'Build world-class Android apps for millions of users with clean code and great UX.',
             '["Develop Android apps using Kotlin","Integrate REST APIs","Write unit tests"]',
             '["1+ years Android development","Kotlin knowledge","Android Studio experience"]',
             '["Kotlin","Java","Android SDK","MVVM","REST APIs","Firebase"]',
             'https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg', 1, 150),
        ]
        try:
            raw = conn._conn
            cur = raw.cursor()
            cur.executemany("""
                INSERT INTO jobs
                    (recruiter_id, title, company, location, salary, job_type, category,
                     experience, work_mode, description, responsibilities, requirements,
                     skills, logo_url, is_active, views)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, jobs)
            raw.commit()
            print("[DB] Sample jobs inserted.")
        except Exception as e:
            print(f"[DB] Error inserting jobs: {e}")
