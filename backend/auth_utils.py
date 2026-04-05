"""
auth_utils.py
JWT token generation/verification and password hashing using stdlib only.
"""

import jwt
import hashlib
import os
import datetime
from functools import wraps
from flask import request, jsonify

JWT_SECRET  = os.environ.get('JWT_SECRET_KEY', 'jwt_jobhub_secret_2026')
JWT_ALGO    = 'HS256'
JWT_EXPIRES = 24  # hours


# ── PASSWORD ──────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    """SHA-256 hash of password. In production use bcrypt."""
    return hashlib.sha256(plain.encode('utf-8')).hexdigest()


def check_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ── JWT ───────────────────────────────────────────────────────────────
def generate_token(user_id: int, email: str, role: str, name: str) -> str:
    payload = {
        'sub':   str(user_id),
        'email': email,
        'role':  role,
        'name':  name,
        'iat':   datetime.datetime.utcnow(),
        'exp':   datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    """Decode and verify JWT. Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError."""
    data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    if 'sub' in data and isinstance(data['sub'], str) and data['sub'].isdigit():
        data['sub'] = int(data['sub'])
    return data


# ── DECORATORS ────────────────────────────────────────────────────────
def token_required(f):
    """Route decorator: requires valid Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
                
        if not token:
            return jsonify({'error': 'Missing or invalid Authorization header or token parameter'}), 401
        try:
            data = decode_token(token)
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired. Please login again.'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401

        return f(*args, **kwargs)
    return decorated


def recruiter_required(f):
    """Route decorator: requires valid token AND recruiter role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
                
        if not token:
            return jsonify({'error': 'Missing or invalid Authorization header or token parameter'}), 401
        try:
            data = decode_token(token)
            if data.get('role') != 'recruiter':
                return jsonify({'error': 'Recruiter access required'}), 403
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated


def jobseeker_required(f):
    """Route decorator: requires valid token AND jobseeker role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
                
        if not token:
            return jsonify({'error': 'Missing or invalid Authorization header or token parameter'}), 401
        try:
            data = decode_token(token)
            if data.get('role') != 'jobseeker':
                return jsonify({'error': 'Job seeker access required'}), 403
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Route decorator: requires valid token AND admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
                
        if not token:
            return jsonify({'error': 'Missing or invalid Authorization header or token parameter'}), 401
        try:
            data = decode_token(token)
            if data.get('role') != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            request.current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated




def optional_token(f):
    """Route decorator: attaches user if token present, continues if not."""
    @wraps(f)
    def decorated(*args, **kwargs):
        request.current_user = None
        auth_header = request.headers.get('Authorization', '')
        token = request.args.get('token')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            
        if token:
            try:
                request.current_user = decode_token(token)
            except Exception:
                pass
        return f(*args, **kwargs)
    return decorated


# -- AVATAR FILE HANDLING ----------------------------------
def save_avatar_file(file, user_id):
    """Save uploaded avatar file and return URL/path."""
    from werkzeug.utils import secure_filename
    from PIL import Image
    import io
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if not file or file.filename == '':
        raise ValueError('No file selected')
    
    if not allowed_file(file.filename):
        raise ValueError('File type not allowed. Use JPG, PNG, GIF, or WebP')
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Read the file
    file.seek(0)
    file_data = file.read()
    
    if len(file_data) > 5 * 1024 * 1024:  # 5MB max
        raise ValueError('File too large! Maximum 5MB allowed')
    
    # Validate image and optimize
    try:
        img = Image.open(io.BytesIO(file_data))
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Resize to max 600x600
        max_size = (600, 600)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Generate filename
        filename = f"avatar_{user_id}.jpg"
        filepath = os.path.join(upload_dir, filename)
        
        # Save as JPEG
        img.save(filepath, 'JPEG', quality=85, optimize=True)
        
        # Return URL path (relative to uploads)
        return f"/uploads/{filename}"
    
    except Exception as e:
        raise ValueError(f'Invalid image file: {str(e)}')
