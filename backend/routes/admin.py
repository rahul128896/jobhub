"""
routes/admin.py
===============
Admin-only endpoints: platform statistics, user/job/application management.

MySQL note: all SQL placeholders use %s (not ?).
COUNT(*) queries use an alias (AS n) so results come back as row['n'].
"""

from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import admin_required

admin_bp = Blueprint('admin', __name__)


# ── PLATFORM STATS ────────────────────────────────────────────────────
@admin_bp.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_stats():
    conn = get_db()
    try:
        def count(sql, params=None):
            """Helper: run a COUNT query and return the integer result."""
            row = conn.execute(sql, params).fetchone()
            # PyMySQL DictCursor returns {'n': value} when you alias the column
            return row['n'] if row else 0

        total_users      = count("SELECT COUNT(*) AS n FROM users WHERE role != 'admin'")
        total_seekers    = count("SELECT COUNT(*) AS n FROM users WHERE role = 'jobseeker'")
        total_recruiters = count("SELECT COUNT(*) AS n FROM users WHERE role = 'recruiter'")
        total_jobs       = count("SELECT COUNT(*) AS n FROM jobs")
        active_jobs      = count("SELECT COUNT(*) AS n FROM jobs WHERE is_active = 1")
        total_apps       = count("SELECT COUNT(*) AS n FROM applications")
        hired            = count("SELECT COUNT(*) AS n FROM applications WHERE status = 'Hired'")
        shortlisted      = count("SELECT COUNT(*) AS n FROM applications WHERE status = 'Shortlisted'")

        return jsonify({
            'total_users':      total_users,
            'total_seekers':    total_seekers,
            'total_recruiters': total_recruiters,
            'total_jobs':       total_jobs,
            'active_jobs':      active_jobs,
            'total_apps':       total_apps,
            'hired':            hired,
            'shortlisted':      shortlisted,
        }), 200
    finally:
        conn.close()


# ── ALL USERS ─────────────────────────────────────────────────────────
@admin_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, name, email, role, phone, location, created_at "
            "FROM users ORDER BY created_at DESC"
        ).fetchall()

        users = [{
            'id':         r['id'],
            'name':       r['name'],
            'email':      r['email'],
            'role':       r['role'],
            'phone':      r.get('phone'),
            'location':   r.get('location'),
            'created_at': str(r.get('created_at', '')),
        } for r in rows]

        return jsonify({'users': users}), 200
    finally:
        conn.close()


# ── DELETE USER ───────────────────────────────────────────────────────
@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    conn = get_db()
    try:
        user = conn.execute(
            'SELECT id, role FROM users WHERE id = %s', (user_id,)
        ).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user['role'] == 'admin':
            return jsonify({'error': 'Cannot delete admin accounts'}), 403

        conn.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    finally:
        conn.close()


# ── ALL JOBS ──────────────────────────────────────────────────────────
@admin_bp.route('/api/admin/jobs', methods=['GET'])
@admin_required
def get_jobs():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT
                j.id, j.title, j.company, j.location, j.job_type,
                j.is_active, j.views, j.created_at,
                u.name AS recruiter_name,
                (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.id) AS applicant_count
            FROM jobs j
            JOIN users u ON u.id = j.recruiter_id
            ORDER BY j.created_at DESC
        """).fetchall()

        jobs = [{
            'id':              r['id'],
            'title':           r['title'],
            'company':         r['company'],
            'location':        r['location'],
            'type':            r['job_type'],
            'is_active':       bool(r['is_active']),
            'views':           r['views'],
            'created_at':      str(r.get('created_at', '')),
            'recruiter_name':  r.get('recruiter_name'),
            'applicant_count': r.get('applicant_count', 0),
        } for r in rows]

        return jsonify({'jobs': jobs}), 200
    finally:
        conn.close()


# ── DELETE JOB ────────────────────────────────────────────────────────
@admin_bp.route('/api/admin/jobs/<int:job_id>', methods=['DELETE'])
@admin_required
def delete_job(job_id):
    conn = get_db()
    try:
        job = conn.execute(
            'SELECT id FROM jobs WHERE id = %s', (job_id,)
        ).fetchone()
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        conn.execute('DELETE FROM jobs WHERE id = %s', (job_id,))
        conn.commit()
        return jsonify({'message': 'Job deleted successfully'}), 200
    finally:
        conn.close()


# ── TOGGLE JOB ACTIVE STATUS ──────────────────────────────────────────
@admin_bp.route('/api/admin/jobs/<int:job_id>/toggle', methods=['PUT'])
@admin_required
def toggle_job(job_id):
    conn = get_db()
    try:
        job = conn.execute(
            'SELECT id, is_active FROM jobs WHERE id = %s', (job_id,)
        ).fetchone()
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        new_status = 0 if job['is_active'] else 1
        conn.execute(
            'UPDATE jobs SET is_active = %s WHERE id = %s', (new_status, job_id)
        )
        conn.commit()
        return jsonify({'message': 'Job status updated', 'is_active': bool(new_status)}), 200
    finally:
        conn.close()


# ── ALL APPLICATIONS ──────────────────────────────────────────────────
@admin_bp.route('/api/admin/applications', methods=['GET'])
@admin_required
def get_applications():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT
                a.id, a.status, a.applied_at,
                a.name  AS applicant_name,
                a.email AS applicant_email,
                j.title AS job_title,
                j.company
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            ORDER BY a.applied_at DESC
            LIMIT 200
        """).fetchall()

        apps = [{
            'id':              r['id'],
            'status':          r['status'],
            'applied_at':      str(r.get('applied_at', '')),
            'applicant_name':  r.get('applicant_name'),
            'applicant_email': r.get('applicant_email'),
            'job_title':       r.get('job_title'),
            'company':         r.get('company'),
        } for r in rows]

        return jsonify({'applications': apps}), 200
    finally:
        conn.close()
