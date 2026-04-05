"""
app.py — Main Flask application for JobHub Job Portal
Tech Stack: Python + Flask + SQLite (MySQL-ready) + JWT Auth
"""

import os
import sys

# Load .env first
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, jsonify, send_from_directory, request
from database import init_db, DB_PATH
from extensions import mail

# ── APP FACTORY ───────────────────────────────────────────────────────
def create_app():
    # Serve frontend from ../frontend directory
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    frontend_dir = os.path.abspath(frontend_dir)

    app = Flask(
        __name__,
        static_folder=frontend_dir,
        static_url_path=''
    )

    # ── CONFIG ────────────────────────────────────────────────────────
    app.config['SECRET_KEY']         = os.environ.get('SECRET_KEY', 'dev_secret_change_me')
    app.config['JWT_SECRET_KEY']     = os.environ.get('JWT_SECRET_KEY', 'jwt_secret_change_me')
    app.config['UPLOAD_FOLDER']      = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))
    app.config['DATABASE_PATH']      = os.environ.get('DATABASE_PATH', 'jobhub.db')
    app.config['FRONTEND_DIR']       = frontend_dir

    # ── FLASK MAIL CONFIG ─────────────────────────────────────────────
    app.config['MAIL_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('SENDER_EMAIL')
    app.config['MAIL_PASSWORD'] = os.environ.get('SENDER_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = f"{os.environ.get('SENDER_NAME', 'JobHub')} <{os.environ.get('SENDER_EMAIL')}>"
    
    mail.init_app(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── CORS (manual, no flask-cors needed) ───────────────────────────
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Origin']  = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS,PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

    @app.before_request
    def handle_preflight():
        if request.method == 'OPTIONS':
            from flask import make_response
            resp = make_response()
            resp.status_code = 200
            return resp

    # ── REGISTER BLUEPRINTS ───────────────────────────────────────────
    from routes.auth         import auth_bp
    from routes.jobs         import jobs_bp
    from routes.applications import applications_bp
    from routes.admin        import admin_bp
    from routes.chat         import chat_bp
    from routes.ai           import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(ai_bp)


    # ── HEALTH CHECK ──────────────────────────────────────────────────
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            'status':   'ok',
            'message':  'JobHub API is running',
            'version':  '1.0.0',
            'database': DB_PATH,
        }), 200

    # ── FRONTEND STATIC ROUTES ────────────────────────────────────────
    # Serve uploads (avatars, resumes, etc)
    @app.route('/uploads/<filename>')
    def serve_upload(filename):
        uploads_dir = app.config['UPLOAD_FOLDER']
        return send_from_directory(uploads_dir, filename)

    # Serve HTML pages
    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_frontend(path):
        full_path = os.path.join(frontend_dir, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(frontend_dir, path)
        # SPA fallback
        return send_from_directory(frontend_dir, 'index.html')

    # ── ERROR HANDLERS ────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        return send_from_directory(frontend_dir, 'index.html')

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({'error': 'File too large. Maximum size is 5MB'}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

    return app


# ── MAIN ──────────────────────────────────────────────────────────────
app = create_app()

if __name__ == '__main__':
    print("=" * 55)
    print("  JobHub API Server")
    print("=" * 55)

    # Initialize DB
    print("[*] Initializing database...")
    init_db()

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    print(f"[*] Frontend dir: {app.config['FRONTEND_DIR']}")
    print(f"[*] Upload dir:   {app.config['UPLOAD_FOLDER']}")
    print(f"[*] Starting server on http://localhost:{port}")
    print("=" * 55)
    print("  Demo Accounts:")
    print("  Job Seeker: rahul@example.com / password123")
    print("  Recruiter:  recruiter@google.com / recruiter123")
    print("  Admin:      admin@jobhub.com / admin123")
    print("=" * 55)

    app.run(host='0.0.0.0', port=port, debug=debug)
