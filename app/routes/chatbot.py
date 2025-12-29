from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from google import genai  # NEW: Unified SDK
from google.genai import types
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the new Client
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    logger.warning("⚠️ GEMINI_API_KEY not set. Chatbot is in fallback mode.")

# System prompt for BatteryMate AI
SYSTEM_PROMPT = """You are BatteryMate, an AI assistant for electric vehicle (EV) drivers in India. 
Help with: 🔋 Battery health, ⚡ Charging, 🌍 Eco-driving, and 🗺️ Route optimization.

Rules:
- Keep responses friendly and under 150 words.
- Always use emojis.
- If asked about non-EV topics (like Mumbai AQI), answer concisely but mention how it affects EV driving (e.g., how high pollution might impact cabin air filter maintenance or route efficiency).
"""

def get_gemini_response(user_message):
    """
    ✅ Using the latest Gemini 2.5 Flash model
    """
    if not client:
        return "👋 I'm BatteryMate! I'm in fallback mode. Ask me about EV charging tips!"

    try:
        # The new SDK uses client.models.generate_content
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=350,
                temperature=0.7,
            )
        )
        
        if response and response.text:
            return response.text.strip()
        return "I'm having a quick recharge break! 🔋 Ask me another EV question."

    except Exception as e:
        logger.error(f"Gemini SDK Error: {e}")
        return "⚠️ Service temporarily unavailable. Let's talk about your EV range later! ⚡"

@chatbot_bp.route('/message', methods=['POST'])
@jwt_required()
def chat_message():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'reply': '❌ Please type a message!'}), 400
        
        # Get response from new SDK
        reply = get_gemini_response(user_message)
        
        return jsonify({
            'success': True,
            'reply': reply,
            'user_id': user_id
        }), 200
    
    except Exception as e:
        logger.error(f"Chatbot endpoint error: {e}")
        return jsonify({'success': False, 'reply': '❌ Something went wrong on the server.'}), 500

@chatbot_bp.route('/health', methods=['GET'])
def chatbot_health():
    return jsonify({
        'status': 'healthy',
        'sdk': 'google-genai 1.56.0',
        'model': 'gemini-2.5-flash'
    }), 200