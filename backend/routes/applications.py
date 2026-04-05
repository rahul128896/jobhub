"""
routes/applications.py
======================
Application endpoints:
  POST /api/apply
  GET  /api/my-applications
  GET  /api/recruiter/jobs/<id>/applications
  GET  /api/recruiter/applicants
  PUT  /api/application/<id>/status
  GET  /api/resume/<filename>

MySQL note: all SQL placeholders use %s (not ?).
PyMySQL DictCursor rows are plain dicts, so use .get() for optional keys.
"""

import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from database import get_db
from auth_utils import token_required, recruiter_required

applications_bp = Blueprint('applications', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def app_to_dict(row) -> dict:
    """Convert a DB row to a JSON-safe application dict."""
    return {
        'id':              row['id'],
        'job_id':          row['job_id'],
        'seeker_id':       row['seeker_id'],
        'name':            row['name'],
        'email':           row['email'],
        'phone':           row.get('phone'),
        'linkedin':        row.get('linkedin'),
        'portfolio':       row.get('portfolio'),
        'experience':      row.get('experience'),
        'cover_letter':    row.get('cover_letter'),
        'resume_filename': row.get('resume_filename'),
        'resume_path':     row.get('resume_path'),
        'status':          row['status'],
        'applied_at':      str(row.get('applied_at', '')),
        # These fields only exist on JOIN queries
        'job_title':       row.get('job_title'),
        'job_company':     row.get('job_company'),
        'job_logo':        row.get('job_logo'),
        'job_location':    row.get('job_location'),
        'applicant_name':  row.get('applicant_name'),
        'applicant_email': row.get('applicant_email'),
    }


# ── APPLY FOR JOB ─────────────────────────────────────────────────────
@applications_bp.route('/api/apply', methods=['POST'])
@token_required
def apply_for_job():
    user_id = request.current_user['sub']
    role    = request.current_user.get('role')

    if role != 'jobseeker':
        return jsonify({'error': 'Only job seekers can apply for jobs'}), 403

    # Support both JSON and multipart form
    if request.content_type and 'multipart/form-data' in request.content_type:
        job_id       = request.form.get('job_id')
        name         = request.form.get('name', '').strip()
        email        = request.form.get('email', '').strip()
        phone        = request.form.get('phone', '').strip()
        linkedin     = request.form.get('linkedin', '').strip()
        portfolio    = request.form.get('portfolio', '').strip()
        experience   = request.form.get('experience', '').strip()
        cover_letter = request.form.get('cover_letter', '').strip()
    else:
        data         = request.get_json(silent=True) or {}
        job_id       = data.get('job_id')
        name         = data.get('name', '').strip()
        email        = data.get('email', '').strip()
        phone        = data.get('phone', '').strip()
        linkedin     = data.get('linkedin', '').strip()
        portfolio    = data.get('portfolio', '').strip()
        experience   = data.get('experience', '').strip()
        cover_letter = data.get('cover_letter', '').strip()

    if not job_id or not name or not email:
        return jsonify({'error': 'Job ID, name, and email are required'}), 422

    # Handle resume upload
    resume_filename = None
    resume_path     = None
    if 'resume' in request.files:
        file = request.files['resume']
        if file and file.filename and allowed_file(file.filename):
            ext       = file.filename.rsplit('.', 1)[1].lower()
            safe_name = f"resume_{user_id}_{job_id}_{uuid.uuid4().hex[:8]}.{ext}"
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, safe_name))
            resume_filename = file.filename
            resume_path     = safe_name
        elif file and file.filename:
            return jsonify({'error': 'Only PDF, DOC, DOCX files are allowed'}), 422

    conn = get_db()
    try:
        job = conn.execute(
            'SELECT id, title, company FROM jobs WHERE id = %s', (job_id,)
        ).fetchone()
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        existing = conn.execute(
            'SELECT id FROM applications WHERE job_id = %s AND seeker_id = %s',
            (job_id, user_id)
        ).fetchone()
        if existing:
            return jsonify({'error': 'You have already applied for this job'}), 409

        conn.execute("""
            INSERT INTO applications
                (job_id, seeker_id, name, email, phone, linkedin, portfolio,
                 experience, cover_letter, resume_filename, resume_path)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (job_id, user_id, name, email, phone, linkedin, portfolio,
              experience, cover_letter, resume_filename, resume_path))
        conn.commit()

        return jsonify({
            'message':    f'Application submitted for {job["title"]} at {job["company"]}',
            'job_title':   job['title'],
            'job_company': job['company'],
        }), 201

    finally:
        conn.close()


# ── SEEKER: MY APPLICATIONS ───────────────────────────────────────────
@applications_bp.route('/api/my-applications', methods=['GET'])
@token_required
def my_applications():
    user_id = request.current_user['sub']
    conn    = get_db()
    try:
        rows = conn.execute("""
            SELECT
                a.*,
                j.title    AS job_title,
                j.company  AS job_company,
                j.logo_url AS job_logo,
                j.location AS job_location
            FROM applications a
            INNER JOIN jobs j ON j.id = a.job_id
            WHERE a.seeker_id = %s
            ORDER BY a.applied_at DESC
        """, (user_id,)).fetchall()

        apps = []
        for r in rows:
            d = app_to_dict(r)
            d['title']       = r.get('job_title')
            d['company']     = r.get('job_company')
            d['logo']        = r.get('job_logo')
            d['location']    = r.get('job_location')
            d['appliedDate'] = str(r.get('applied_at', ''))
            apps.append(d)

        return jsonify({'applications': apps}), 200
    finally:
        conn.close()


# ── RECRUITER: APPLICATIONS FOR A JOB ────────────────────────────────
@applications_bp.route('/api/recruiter/jobs/<int:job_id>/applications', methods=['GET'])
@recruiter_required
def job_applications(job_id):
    user_id = request.current_user['sub']
    conn    = get_db()
    try:
        # Verify recruiter owns this job
        job = conn.execute(
            'SELECT id FROM jobs WHERE id = %s AND recruiter_id = %s',
            (job_id, user_id)
        ).fetchone()
        if not job:
            return jsonify({'error': 'Job not found or unauthorized'}), 404

        rows = conn.execute("""
            SELECT
                a.*,
                u.name   AS applicant_name,
                u.email  AS applicant_email,
                u.avatar AS applicant_avatar
            FROM applications a
            INNER JOIN users u ON u.id = a.seeker_id
            WHERE a.job_id = %s
            ORDER BY a.applied_at DESC
        """, (job_id,)).fetchall()

        return jsonify({'applications': [app_to_dict(r) for r in rows]}), 200
    finally:
        conn.close()


# ── RECRUITER: ALL APPLICANTS ─────────────────────────────────────────
@applications_bp.route('/api/recruiter/applicants', methods=['GET'])
@recruiter_required
def all_applicants():
    user_id = request.current_user['sub']
    conn    = get_db()
    try:
        rows = conn.execute("""
            SELECT
                a.*,
                j.title   AS job_title,
                j.company AS job_company,
                u.name    AS applicant_name,
                u.email   AS applicant_email
            FROM applications a
            INNER JOIN jobs j ON j.id = a.job_id
            INNER JOIN users u ON u.id = a.seeker_id
            WHERE j.recruiter_id = %s
            ORDER BY a.applied_at DESC
        """, (user_id,)).fetchall()

        return jsonify({'applications': [app_to_dict(r) for r in rows]}), 200
    finally:
        conn.close()


# ── UPDATE APPLICATION STATUS (recruiter) ─────────────────────────────
@applications_bp.route('/api/application/<int:app_id>/status', methods=['PUT'])
@recruiter_required
def update_status(app_id):
    user_id = request.current_user['sub']
    data    = request.get_json(silent=True) or {}
    status  = data.get('status', '').strip()

    allowed = ('Under Review', 'Shortlisted', 'Hired', 'Rejected')
    if status not in allowed:
        return jsonify({'error': f'Status must be one of: {", ".join(allowed)}'}), 422

    conn = get_db()
    try:
        # Only allow recruiter to update status for jobs they own
        app = conn.execute("""
            SELECT a.id FROM applications a
            INNER JOIN jobs j ON j.id = a.job_id
            WHERE a.id = %s AND j.recruiter_id = %s
        """, (app_id, user_id)).fetchone()

        if not app:
            return jsonify({'error': 'Application not found or unauthorized'}), 404

        conn.execute(
            'UPDATE applications SET status = %s WHERE id = %s',
            (status, app_id)
        )
        conn.commit()
        return jsonify({'message': f'Status updated to: {status}'}), 200
    finally:
        conn.close()


# ── DOWNLOAD RESUME ───────────────────────────────────────────────────
@applications_bp.route('/api/resume/<filename>', methods=['GET'])
@token_required
def download_resume(filename):
    role    = request.current_user.get('role')
    user_id = request.current_user['sub']

    conn = get_db()
    try:
        app = conn.execute(
            'SELECT * FROM applications WHERE resume_path = %s', (filename,)
        ).fetchone()
        if not app:
            return jsonify({'error': 'Resume not found'}), 404

        if role == 'jobseeker' and app['seeker_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        if role == 'recruiter':
            job = conn.execute(
                'SELECT id FROM jobs WHERE id = %s AND recruiter_id = %s',
                (app['job_id'], user_id)
            ).fetchone()
            if not job:
                return jsonify({'error': 'Unauthorized'}), 403

        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return send_from_directory(
            upload_dir, filename,
            as_attachment=True,
            download_name=app.get('resume_filename') or filename
        )
    finally:
        conn.close()
