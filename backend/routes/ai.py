from flask import Blueprint, request, jsonify
from services.resume_analyzer import extract_text, analyze_resume, match_jobs
from auth_utils import optional_token

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/api/upload-resume', methods=['POST'])
@optional_token
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    # Check max file size dynamically (2MB limiting protection)
    file.seek(0, 2) 
    file_length = file.tell()
    if file_length > 2 * 1024 * 1024:
        return jsonify({"error": "File size exceeds the 2MB limit!"}), 413
    file.seek(0)
    
    text = extract_text(file, file.filename)
    if not text:
        return jsonify({"error": "Failed to extract text. Unrecognized format or corrupted document. Please only drop PDF or DOCX files!"}), 400
        
    if len(text) < 50:
        return jsonify({"error": "The detected document text is too incredibly short to analyze realistically."}), 400
        
    ai_data = analyze_resume(text)
    if not ai_data:
        return jsonify({"error": "The Gemini engine failed to process this document. Either an API error occurred natively or the API keys weren't configured!"}), 500
        
    skills = ai_data.get('skills', [])
    experience = ai_data.get('experience', 'Unknown')
    roles = ai_data.get('roles', [])
    
    recommended_jobs = []
    if skills:
        recommended_jobs = match_jobs(skills)
        
    return jsonify({
        "success": True,
        "skills": skills,
        "experience": experience,
        "roles": roles,
        "recommended_jobs": recommended_jobs
    }), 200
