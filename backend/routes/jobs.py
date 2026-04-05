"""
routes/jobs.py
==============
Job listing endpoints: browse, search, filter, CRUD for recruiters.

MySQL note: all SQL placeholders use %s (not ? like SQLite).
COUNT(*) rows return as {'COUNT(*)': n} with PyMySQL DictCursor.
CAST salary sort uses DECIMAL instead of SQLite's REAL.
"""

import json
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required, recruiter_required, optional_token

jobs_bp = Blueprint('jobs', __name__)


# ── HELPERS ──────────────────────────────────────────────────────────
def job_to_dict(row) -> dict:
    """Convert a DB row dict to a JSON-safe job dict."""

    def parse_json_field(value):
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [s.strip() for s in value.split(',') if s.strip()]
        return value or []

    return {
        'id':              row['id'],
        'recruiter_id':    row['recruiter_id'],
        'title':           row['title'],
        'company':         row['company'],
        'location':        row['location'],
        'salary':          row.get('salary'),
        'type':            row['job_type'],
        'category':        row['category'],
        'exp':             row['experience'],
        'mode':            row['work_mode'],
        'description':     row.get('description'),
        'responsibilities': parse_json_field(row.get('responsibilities')),
        'requirements':    parse_json_field(row.get('requirements')),
        'skills':          parse_json_field(row.get('skills')),
        'logo':            row.get('logo_url') or '',
        'is_active':       bool(row['is_active']),
        'views':           row['views'],
        'posted':          str(row['created_at']),
        'created_at':      str(row['created_at']),
    }


# ── GET ALL JOBS (public, with filters) ──────────────────────────────
@jobs_bp.route('/api/jobs', methods=['GET'])
@optional_token
def get_jobs():
    q         = request.args.get('q', '').strip()
    location  = request.args.get('location', '').strip()
    category  = request.args.get('category', '').strip()
    job_type  = request.args.get('type', '').strip()
    work_mode = request.args.get('mode', '').strip()
    exp       = request.args.get('exp', '').strip()
    sort      = request.args.get('sort', 'latest')
    page      = int(request.args.get('page', 1))
    per_page  = int(request.args.get('per_page', 20))

    # Build WHERE clause dynamically
    conditions = ['is_active = 1']
    params     = []

    if q:
        conditions.append('(title LIKE %s OR company LIKE %s OR skills LIKE %s)')
        like = f'%{q}%'
        params += [like, like, like]
    if location:
        conditions.append('location LIKE %s')
        params.append(f'%{location}%')
    if category:
        conditions.append('category = %s')
        params.append(category)
    if job_type:
        conditions.append('job_type = %s')
        params.append(job_type)
    if work_mode:
        conditions.append('work_mode = %s')
        params.append(work_mode)
    if exp:
        conditions.append('experience = %s')
        params.append(exp)

    where = 'WHERE ' + ' AND '.join(conditions)

    # Salary sort: MySQL uses DECIMAL (not SQLite's REAL)
    if sort == 'salary-high':
        order = "ORDER BY CAST(REPLACE(REPLACE(salary, '₹', ''), ' LPA', '') AS DECIMAL(10,2)) DESC"
    elif sort == 'salary-low':
        order = "ORDER BY CAST(REPLACE(REPLACE(salary, '₹', ''), ' LPA', '') AS DECIMAL(10,2)) ASC"
    else:
        order = "ORDER BY created_at DESC"

    conn = get_db()
    try:
        # Total count
        count_row = conn.execute(
            f"SELECT COUNT(*) AS total FROM jobs {where}", params
        ).fetchone()
        total_rows = count_row['total']

        # Paginated results
        offset = (page - 1) * per_page
        rows   = conn.execute(
            f"SELECT * FROM jobs {where} {order} LIMIT %s OFFSET %s",
            params + [per_page, offset]
        ).fetchall()

        return jsonify({
            'jobs':     [job_to_dict(r) for r in rows],
            'total':    total_rows,
            'page':     page,
            'per_page': per_page,
            'pages':    (total_rows + per_page - 1) // per_page,
        }), 200
    finally:
        conn.close()


# ── GET SINGLE JOB ────────────────────────────────────────────────────
@jobs_bp.route('/api/jobs/<int:job_id>', methods=['GET'])
@optional_token
def get_job(job_id):
    conn = get_db()
    try:
        job = conn.execute(
            'SELECT * FROM jobs WHERE id = %s', (job_id,)
        ).fetchone()
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        # Increment view count
        conn.execute('UPDATE jobs SET views = views + 1 WHERE id = %s', (job_id,))
        conn.commit()

        return jsonify({'job': job_to_dict(job)}), 200
    finally:
        conn.close()


# ── POST NEW JOB (recruiter only) ─────────────────────────────────────
@jobs_bp.route('/api/jobs', methods=['POST'])
@recruiter_required
def create_job():
    data    = request.get_json(silent=True) or {}
    user_id = request.current_user['sub']

    title       = data.get('title', '').strip()
    company     = data.get('company', '').strip()
    location    = data.get('location', '').strip()
    salary      = data.get('salary', '').strip()
    job_type    = data.get('job_type') or data.get('type', 'Full-time')
    category    = data.get('category', 'Engineering')
    experience  = data.get('experience') or data.get('exp', '1-3 years')
    work_mode   = data.get('work_mode') or data.get('mode', 'On-site')
    description = data.get('description', '').strip()
    skills_raw  = data.get('skills', [])
    resp_raw    = data.get('responsibilities', [])
    req_raw     = data.get('requirements', [])
    logo_url    = data.get('logo_url', '').strip()

    if not title or not company or not location:
        return jsonify({'error': 'Title, company, and location are required'}), 422

    # Store lists as JSON strings in the database
    skills = (
        json.dumps([s.strip() for s in skills_raw.split(',') if s.strip()])
        if isinstance(skills_raw, str) else json.dumps(skills_raw)
    )
    responsibilities = json.dumps(resp_raw) if isinstance(resp_raw, list) else resp_raw
    requirements     = json.dumps(req_raw)  if isinstance(req_raw,  list) else req_raw

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO jobs
                (recruiter_id, title, company, location, salary, job_type,
                 category, experience, work_mode, description,
                 responsibilities, requirements, skills, logo_url)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (user_id, title, company, location, salary, job_type, category,
              experience, work_mode, description, responsibilities, requirements,
              skills, logo_url))
        conn.commit()

        new_id = conn.lastrowid
        job    = conn.execute('SELECT * FROM jobs WHERE id = %s', (new_id,)).fetchone()
        return jsonify({'message': 'Job posted successfully', 'job': job_to_dict(job)}), 201
    finally:
        conn.close()


# ── UPDATE JOB ────────────────────────────────────────────────────────
@jobs_bp.route('/api/jobs/<int:job_id>', methods=['PUT'])
@recruiter_required
def update_job(job_id):
    user_id = request.current_user['sub']
    data    = request.get_json(silent=True) or {}

    conn = get_db()
    try:
        job = conn.execute(
            'SELECT * FROM jobs WHERE id = %s', (job_id,)
        ).fetchone()
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        if job['recruiter_id'] != user_id:
            return jsonify({'error': 'Unauthorized: not your job listing'}), 403

        title       = data.get('title',       job['title'])
        company     = data.get('company',     job['company'])
        location    = data.get('location',    job['location'])
        salary      = data.get('salary',      job.get('salary'))
        job_type    = data.get('type',        job['job_type'])
        category    = data.get('category',    job['category'])
        experience  = data.get('exp',         job['experience'])
        work_mode   = data.get('mode',        job['work_mode'])
        description = data.get('description', job.get('description'))
        is_active   = data.get('is_active',   job['is_active'])

        skills_raw = data.get('skills', None)
        skills = (
            json.dumps(skills_raw) if isinstance(skills_raw, list) else skills_raw
        ) if skills_raw is not None else job.get('skills')

        conn.execute("""
            UPDATE jobs
            SET title=%s, company=%s, location=%s, salary=%s, job_type=%s,
                category=%s, experience=%s, work_mode=%s, description=%s,
                skills=%s, is_active=%s
            WHERE id=%s
        """, (title, company, location, salary, job_type, category,
              experience, work_mode, description, skills, is_active, job_id))
        conn.commit()

        job = conn.execute('SELECT * FROM jobs WHERE id = %s', (job_id,)).fetchone()
        return jsonify({'message': 'Job updated', 'job': job_to_dict(job)}), 200
    finally:
        conn.close()


# ── DELETE JOB ────────────────────────────────────────────────────────
@jobs_bp.route('/api/jobs/<int:job_id>', methods=['DELETE'])
@recruiter_required
def delete_job(job_id):
    user_id = request.current_user['sub']
    conn    = get_db()
    try:
        job = conn.execute(
            'SELECT * FROM jobs WHERE id = %s', (job_id,)
        ).fetchone()
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        if job['recruiter_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        conn.execute('DELETE FROM jobs WHERE id = %s', (job_id,))
        conn.commit()
        return jsonify({'message': 'Job deleted successfully'}), 200
    finally:
        conn.close()


# ── RECRUITER: GET MY JOBS ────────────────────────────────────────────
@jobs_bp.route('/api/recruiter/jobs', methods=['GET'])
@recruiter_required
def get_recruiter_jobs():
    user_id = request.current_user['sub']
    conn    = get_db()
    try:
        rows = conn.execute(
            'SELECT * FROM jobs WHERE recruiter_id = %s ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()

        jobs = []
        for r in rows:
            j = job_to_dict(r)
            count = conn.execute(
                'SELECT COUNT(*) AS n FROM applications WHERE job_id = %s', (r['id'],)
            ).fetchone()['n']
            j['applicants'] = count
            jobs.append(j)

        return jsonify({'jobs': jobs}), 200
    finally:
        conn.close()


# ── SAVE / UNSAVE JOB ─────────────────────────────────────────────────
@jobs_bp.route('/api/jobs/<int:job_id>/save', methods=['POST'])
@token_required
def save_job(job_id):
    user_id = request.current_user['sub']
    conn    = get_db()
    try:
        existing = conn.execute(
            'SELECT id FROM saved_jobs WHERE user_id = %s AND job_id = %s',
            (user_id, job_id)
        ).fetchone()

        if existing:
            conn.execute(
                'DELETE FROM saved_jobs WHERE user_id = %s AND job_id = %s',
                (user_id, job_id)
            )
            conn.commit()
            return jsonify({'message': 'Job removed from saved list', 'saved': False}), 200
        else:
            conn.execute(
                'INSERT INTO saved_jobs (user_id, job_id) VALUES (%s, %s)',
                (user_id, job_id)
            )
            conn.commit()
            return jsonify({'message': 'Job saved successfully', 'saved': True}), 200
    finally:
        conn.close()


# ── GET SAVED JOBS ────────────────────────────────────────────────────
@jobs_bp.route('/api/saved-jobs', methods=['GET'])
@token_required
def get_saved_jobs():
    user_id = request.current_user['sub']
    conn    = get_db()
    try:
        rows = conn.execute("""
            SELECT j.* FROM jobs j
            INNER JOIN saved_jobs sj ON sj.job_id = j.id
            WHERE sj.user_id = %s
            ORDER BY sj.saved_at DESC
        """, (user_id,)).fetchall()

        return jsonify({'jobs': [job_to_dict(r) for r in rows]}), 200
    finally:
        conn.close()
