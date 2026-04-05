"""
routes/auth.py
==============
Authentication endpoints:
  POST /api/register          ← Step 1: validate input, send OTP
  POST /api/register/verify-otp  ← Step 2: verify OTP, create account
  POST /api/login         ← Simple login (no OTP required)
  POST /api/login/verify-otp  ← Optional 2FA for users with 2FA enabled
  GET  /api/me
  PUT  /api/profile
  PUT  /api/change-password
  PUT  /api/profile-upload
  POST /api/2fa/enable
  POST /api/2fa/verify-enable
  POST /api/2fa/disable
  GET  /api/2fa/status
  POST /api/2fa/resend-otp

MySQL note: all SQL placeholders use %s (not ? like SQLite).
"""

import re
import os
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import hash_password, check_password, generate_token, token_required, save_avatar_file
from otp_utils import generate_otp, store_otp, verify_otp, mark_otp_used
from email_utils import send_otp_email, send_2fa_enabled_email

import datetime
import random
import string
from flask_mail import Message
from extensions import mail

auth_bp = Blueprint('auth', __name__)

OTP_STORE = {}



# ── HELPERS ──────────────────────────────────────────────────────────
def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email))


def user_to_dict(row) -> dict:
    """Convert a DB row (dict from PyMySQL DictCursor) to a JSON-safe dict."""
    return {
        'id':                 row['id'],
        'name':               row['name'],
        'email':              row['email'],
        'role':               row['role'],
        'phone':              row.get('phone'),
        'location':           row.get('location'),
        'bio':                row.get('bio'),
        'linkedin':           row.get('linkedin'),
        'portfolio':          row.get('portfolio'),
        'avatar':             row.get('avatar'),
        'two_factor_enabled': row.get('two_factor_enabled', 0),
        'created_at':         str(row.get('created_at', '')),
    }


# ── SEND OTP (Step 1) ──────────────────────────────────────────────────
@auth_bp.route('/api/send-otp', methods=['POST'])
def send_otp():
    """
    Step 1: Validate input, check if email exists, generate OTP, send via Flask-Mail,
    and store temporarily in OTP_STORE dictionary.
    """
    data = request.get_json(silent=True) or {}

    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role     = data.get('role', '').strip().lower()

    errors = {}
    if not name:
        errors['name'] = 'Full name is required'
    if not email or not is_valid_email(email):
        errors['email'] = 'Valid email is required'
    if not password or len(password) < 6:
        errors['password'] = 'Password must be at least 6 characters'
    if role not in ('jobseeker', 'recruiter'):
        errors['role'] = 'Role must be jobseeker or recruiter'
    if errors:
        return jsonify({'error': 'Validation failed', 'errors': errors}), 422

    conn = get_db()
    try:
        existing = conn.execute(
            'SELECT id FROM users WHERE email = %s', (email,)
        ).fetchone()
        if existing:
            return jsonify({'error': 'Email already registered. Please login.'}), 409

        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP temporarily with 5 min expiry
        expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        OTP_STORE[email] = {
            'otp': otp_code,
            'expires_at': expiry_time
        }

        # Send OTP via Flask-Mail
        try:
            msg = Message(
                subject='Your JobHub Verification Code',
                recipients=[email],
                body=f"Hi {name},\n\nYour JobHub verification code is: {otp_code}\n\nThis code expires in 5 minutes.\n\nBest regards,\nJobHub Team"
            )
            mail.send(msg)
            email_sent = True
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
            email_sent = False

        response = {
            'message': 'Verification code sent to your email. Please verify to complete registration.',
            'requires_otp': True,
            'email': email,
        }
        if not email_sent:
            # Development mode: show OTP in response when SMTP not configured
            response['dev_otp'] = otp_code
            response['warning'] = 'Email not configured or failed to send. OTP shown for development only.'

        return jsonify(response), 200

    finally:
        conn.close()


# ── VERIFY OTP (Step 2) ────────────────────────────────────────────────
@auth_bp.route('/api/verify-otp', methods=['POST'])
def verify_otp_endpoint():
    """
    Step 2: Verify OTP from OTP_STORE and create the user account in MySQL.
    """
    data    = request.get_json(silent=True) or {}
    email   = data.get('email', '').strip().lower()
    otp     = data.get('otp', '').strip()
    name    = data.get('name', '').strip()
    password= data.get('password', '')
    role    = data.get('role', '').strip().lower()

    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 422

    # Check if OTP exists for email
    if email not in OTP_STORE:
        return jsonify({'error': 'No pending OTP found. Please register again.'}), 404

    stored_data = OTP_STORE[email]

    # Check expiry
    if datetime.datetime.utcnow() > stored_data['expires_at']:
        del OTP_STORE[email]
        return jsonify({'error': 'OTP has expired. Please request a new one.'}), 401

    # Verify OTP value
    if stored_data['otp'] != otp:
        return jsonify({'error': 'Invalid verification code'}), 401

    # OTP is valid, store user in DB
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)',
            (name, email, hash_password(password), role)
        )
        conn.commit()

        # Delete temporarily stored OTP
        del OTP_STORE[email]

        # Fetch the created user
        user = conn.execute(
            'SELECT * FROM users WHERE email = %s', (email,)
        ).fetchone()

        token = generate_token(user['id'], user['email'], user['role'], user['name'])
        return jsonify({
            'message': 'Registration successful! Welcome to JobHub.',
            'token':   token,
            'user':    user_to_dict(user),
        }), 201

    finally:
        conn.close()


# ── LOGIN: Verify credentials & issue JWT ───────────────────────────
@auth_bp.route('/api/login', methods=['POST'])
def login():
    """
    Simple login (no OTP required).
    Verifies email + password and returns JWT token directly.
    """
    data     = request.get_json(silent=True) or {}
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 422

    conn = get_db()
    try:
        user = conn.execute(
            'SELECT * FROM users WHERE email = %s', (email,)
        ).fetchone()

        if not user or not check_password(password, user['password']):
            return jsonify({'error': 'Invalid email or password'}), 401

        token = generate_token(user['id'], user['email'], user['role'], user['name'])
        return jsonify({
            'message': 'Login successful',
            'token':   token,
            'user':    user_to_dict(user),
        }), 200

    finally:
        conn.close()


# ── GET CURRENT USER ──────────────────────────────────────────────────
@auth_bp.route('/api/me', methods=['GET'])
@token_required
def get_me():
    user_id = request.current_user['sub']
    conn = get_db()
    try:
        user = conn.execute(
            'SELECT * FROM users WHERE id = %s', (user_id,)
        ).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': user_to_dict(user)}), 200
    finally:
        conn.close()


# ── UPDATE PROFILE ────────────────────────────────────────────────────
@auth_bp.route('/api/profile', methods=['PUT'])
@token_required
def update_profile():
    user_id   = request.current_user['sub']
    data      = request.get_json(silent=True) or {}

    name      = data.get('name', '').strip()
    phone     = data.get('phone', '').strip()
    location  = data.get('location', '').strip()
    bio       = data.get('bio', '').strip()
    linkedin  = data.get('linkedin', '').strip()
    portfolio = data.get('portfolio', '').strip()

    conn = get_db()
    try:
        conn.execute("""
            UPDATE users
            SET name=%s, phone=%s, location=%s, bio=%s, linkedin=%s, portfolio=%s
            WHERE id=%s
        """, (name, phone, location, bio, linkedin, portfolio, user_id))
        conn.commit()

        user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
        return jsonify({'message': 'Profile updated', 'user': user_to_dict(user)}), 200
    finally:
        conn.close()


# ── CHANGE PASSWORD ───────────────────────────────────────────────────
@auth_bp.route('/api/change-password', methods=['PUT'])
@token_required
def change_password():
    user_id = request.current_user['sub']
    data    = request.get_json(silent=True) or {}
    old_pw  = data.get('old_password', '')
    new_pw  = data.get('new_password', '')

    if not old_pw or not new_pw:
        return jsonify({'error': 'Both old and new passwords are required'}), 422
    if len(new_pw) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 422

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
        if not check_password(old_pw, user['password']):
            return jsonify({'error': 'Current password is incorrect'}), 401

        conn.execute(
            'UPDATE users SET password = %s WHERE id = %s',
            (hash_password(new_pw), user_id)
        )
        conn.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    finally:
        conn.close()


# ── UPDATE PROFILE WITH AVATAR ────────────────────────────────────────
@auth_bp.route('/api/profile-upload', methods=['PUT'])
@token_required
def update_profile_upload():
    user_id   = request.current_user['sub']
    name      = request.form.get('name', '').strip()
    phone     = request.form.get('phone', '').strip()
    location  = request.form.get('location', '').strip()
    bio       = request.form.get('bio', '').strip()
    linkedin  = request.form.get('linkedin', '').strip()
    portfolio = request.form.get('portfolio', '').strip()

    avatar_url = None
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename:
            try:
                avatar_url = save_avatar_file(file, user_id)
            except Exception as e:
                return jsonify({'error': f'Avatar upload failed: {str(e)}'}), 400

    conn = get_db()
    try:
        if avatar_url:
            conn.execute("""
                UPDATE users
                SET name=%s, phone=%s, location=%s, bio=%s, linkedin=%s, portfolio=%s, avatar=%s
                WHERE id=%s
            """, (name, phone, location, bio, linkedin, portfolio, avatar_url, user_id))
        else:
            conn.execute("""
                UPDATE users
                SET name=%s, phone=%s, location=%s, bio=%s, linkedin=%s, portfolio=%s
                WHERE id=%s
            """, (name, phone, location, bio, linkedin, portfolio, user_id))
        conn.commit()

        user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found after update'}), 404
        return jsonify({'message': 'Profile updated', 'user': user_to_dict(user)}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500
    finally:
        conn.close()


# ── 2FA: ENABLE ──────────────────────────────────────────────────────
@auth_bp.route('/api/2fa/enable', methods=['POST'])
@token_required
def enable_2fa():
    user_id = request.current_user['sub']
    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user.get('two_factor_enabled'):
            return jsonify({'error': '2FA is already enabled on your account'}), 409

        otp_code = generate_otp()
        if not store_otp(user_id, user['email'], otp_code):
            return jsonify({'error': 'Failed to generate OTP'}), 500

        if not send_otp_email(user['email'], user['name'], otp_code):
            return jsonify({
                'message': 'OTP generated (email not configured)',
                'otp':     otp_code,
                'warning': 'Email not configured. OTP shown for testing.',
            }), 200

        return jsonify({'message': 'OTP sent to your email', 'email': user['email']}), 200
    finally:
        conn.close()


# ── 2FA: VERIFY & ENABLE ─────────────────────────────────────────────
@auth_bp.route('/api/2fa/verify-enable', methods=['POST'])
@token_required
def verify_and_enable_2fa():
    user_id = request.current_user['sub']
    data    = request.get_json(silent=True) or {}
    otp     = data.get('otp', '').strip()

    if not otp:
        return jsonify({'error': 'OTP is required'}), 422

    result = verify_otp(user_id, otp)
    if not result['valid']:
        return jsonify({'error': result['message']}), 401

    mark_otp_used(user_id, otp)

    conn = get_db()
    try:
        conn.execute(
            'UPDATE users SET two_factor_enabled = 1 WHERE id = %s', (user_id,)
        )
        conn.commit()

        user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
        send_2fa_enabled_email(user['email'], user['name'])

        return jsonify({'message': '2FA enabled successfully', 'user': user_to_dict(user)}), 200
    finally:
        conn.close()


# ── 2FA: DISABLE ─────────────────────────────────────────────────────
@auth_bp.route('/api/2fa/disable', methods=['POST'])
@token_required
def disable_2fa():
    user_id  = request.current_user['sub']
    data     = request.get_json(silent=True) or {}
    password = data.get('password', '')

    if not password:
        return jsonify({'error': 'Password is required to disable 2FA'}), 422

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not user.get('two_factor_enabled'):
            return jsonify({'error': '2FA is not enabled on your account'}), 409
        if not check_password(password, user['password']):
            return jsonify({'error': 'Password is incorrect'}), 401

        conn.execute(
            'UPDATE users SET two_factor_enabled = 0 WHERE id = %s', (user_id,)
        )
        conn.commit()

        user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
        return jsonify({'message': '2FA disabled successfully', 'user': user_to_dict(user)}), 200
    finally:
        conn.close()


# ── 2FA: STATUS ──────────────────────────────────────────────────────
@auth_bp.route('/api/2fa/status', methods=['GET'])
@token_required
def get_2fa_status():
    user_id = request.current_user['sub']
    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = %s', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            'two_factor_enabled': user.get('two_factor_enabled', 0),
            'email':              user['email'],
        }), 200
    finally:
        conn.close()


# ── 2FA: RESEND OTP ──────────────────────────────────────────────────
@auth_bp.route('/api/2fa/resend-otp', methods=['POST'])
def resend_otp():
    data  = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()

    if not email or not is_valid_email(email):
        return jsonify({'error': 'Valid email is required'}), 422

    conn = get_db()
    try:
        user = conn.execute(
            'SELECT * FROM users WHERE email = %s', (email,)
        ).fetchone()

        if not user:
            return jsonify({'error': 'User not found or 2FA not enabled'}), 404

        otp_code = generate_otp()
        if not store_otp(user['id'], user['email'], otp_code):
            return jsonify({'error': 'Failed to generate OTP'}), 500

        if not send_otp_email(user['email'], user['name'], otp_code):
            return jsonify({
                'message': 'OTP generated (email not configured)',
                'otp':     otp_code,
                'warning': 'Email not configured. OTP shown for testing.',
            }), 200

        return jsonify({'message': 'OTP resent to your email', 'email': user['email']}), 200
    finally:
        conn.close()
