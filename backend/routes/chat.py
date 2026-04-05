from flask import Blueprint, request, jsonify
from services.chatbot import get_chat_response
from auth_utils import optional_token

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
@optional_token
def chat():
    """
    Endpoint for AI Career Assistant via Gemini.
    Expects JSON: { "message": "user message" }
    Returns JSON: { "reply": "AI response" }
    """
    try:
        data = request.get_json(silent=True) or {}
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'reply': 'Message cannot be empty'}), 400
            
        # Cap message length for safety
        if len(message) > 1000:
            message = message[:1000]
            
        bot_reply = get_chat_response(message)
        
        return jsonify({'reply': bot_reply}), 200
    except Exception as e:
        print(f"[CHAT API ERROR] {e}")
        return jsonify({'reply': 'Internal server error'}), 500
