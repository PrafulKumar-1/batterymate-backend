from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from google import genai
from google.genai import types
import os
import requests

from app.utils.logger import get_logger

logger = get_logger(__name__)

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# API keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')  # set this in env

# Initialize Gemini client
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    logger.warning("⚠️ GEMINI_API_KEY not set. Chatbot is in fallback mode.")

SYSTEM_PROMPT = """
You are BatteryMate, an AI assistant for electric vehicle (EV) drivers in India.

Help with: 🔋 Battery health, ⚡ Charging, 🌍 Eco-driving, and 🗺️ Route optimization.

Rules:
- Keep responses friendly.
- Always use emojis.
- If environment data is provided, you may use it to talk about EV range, comfort,
  and cabin air quality when it is relevant to the user's question.
"""


def get_env_data(lat, lon):
    """Fetch current weather + air pollution for given coordinates using OpenWeather."""
    if not (OPENWEATHER_API_KEY and lat is not None and lon is not None):
        return None

    try:
        # Current weather
        weather_url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        w_resp = requests.get(weather_url, timeout=5)
        w_resp.raise_for_status()
        w = w_resp.json()

        # Air pollution (AQI 1–5, PM2.5, PM10, etc.)[web:4]
        air_url = (
            "https://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        )
        a_resp = requests.get(air_url, timeout=5)
        a_resp.raise_for_status()
        a = a_resp.json()

        weather_desc = w["weather"][0]["description"]
        temp = w["main"]["temp"]
        humidity = w["main"]["humidity"]
        city = w.get("name") or "your area"

        aqi = a["list"][0]["main"]["aqi"]  # 1–5 scale[web:4]
        components = a["list"][0]["components"]

        return {
            "city": city,
            "temp": temp,
            "humidity": humidity,
            "weather": weather_desc,
            "aqi": aqi,
            "pm25": components.get("pm2_5"),
            "pm10": components.get("pm10"),
        }
    except Exception as e:
        logger.error(f"Env data error: {e}")
        return None


def map_aqi_category(aqi_val: int) -> str:
    """Convert OpenWeather AQI (1–5) to a simple text category.[web:4][web:34]"""
    if aqi_val == 1:
        return "good"
    if aqi_val == 2:
        return "fair"
    if aqi_val == 3:
        return "moderate"
    if aqi_val == 4:
        return "poor"
    if aqi_val == 5:
        return "very poor"
    return "unknown"


def user_asked_aqi(user_message: str) -> bool:
    """Detect if the user is asking about AQI / air quality / pollution."""
    text = (user_message or "").lower()
    keywords = [
        "aqi",
        "air quality",
        "air-quality",
        "pollution",
        "pm2.5",
        "pm25",
        "pm 2.5",
        "pm10",
        "pm 10",
        "air index",
        "air pollution",
    ]
    return any(k in text for k in keywords)


def get_gemini_response(user_message: str, env_data=None) -> str:
    """
    - If the user asks about AQI and env_data is available:
        prepend a Python-generated AQI sentence,
        then let Gemini add 3–4 EV-specific sentences.
    - For all other questions:
        just use Gemini's normal answer (with env context available).
    """
    if not client:
        return "👋 I'm BatteryMate! I'm in fallback mode. Ask me about EV charging tips!"

    try:
        asked_aqi = user_asked_aqi(user_message)
        aqi_sentence = ""
        context_block = ""

        if env_data:
            aqi_val = env_data.get("aqi")
            aqi_cat = map_aqi_category(aqi_val)
            city = env_data.get("city")

            # Build AQI sentence ONLY when user explicitly asked
            if asked_aqi and aqi_val is not None:
                aqi_sentence = f"Your current AQI in {city} is {aqi_val} ({aqi_cat}). "

            # Always provide env data as optional context
            context_block = (
                "Environment data for the user's current location:\n"
                f"- Temperature: {env_data.get('temp')} °C\n"
                f"- Humidity: {env_data.get('humidity')}%\n"
                f"- Weather: {env_data.get('weather')}\n"
                f"- PM2.5: {env_data.get('pm25')} µg/m³\n"
                f"- PM10: {env_data.get('pm10')} µg/m³\n\n"
                "Use this information only if it is relevant to the user's question. "
                "Give EV-specific advice when it helps the user."
            )

        # Strong instruction for full replies
        full_contents = (
            "You are answering inside a small chat bubble. "
            "Always write 3–4 complete sentences (around 60–120 words) "
            "and never stop in the middle of a sentence.\n\n"
            f"USER_MESSAGE: {user_message}\n\n{context_block}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=600,  # allow enough tokens[web:63]
                temperature=0.7,
            ),
        )

        model_text = ""
        if response and response.text:
            model_text = response.text.strip()

        #logger.info(f"Gemini raw response: {model_text!r}")

        # If model text is suspiciously short, extend with a generic tail
        if model_text and len(model_text) < 40:
            model_text += (
                " If you want, I can share more details about routes, "
                "charging stops, and EV tips for this trip. 🚗⚡"
            )

        # If we built an AQI sentence, prepend it; otherwise return Gemini text only
        if aqi_sentence:
            return aqi_sentence + (model_text or "")
        else:
            return model_text or "I'm having a quick recharge break! 🔋 Ask me another EV question."
    except Exception as e:
        logger.error(f"Gemini SDK Error: {e}")
        return "⚠️ Service temporarily unavailable. Let's talk about your EV range later! ⚡"


@chatbot_bp.route("/message", methods=["POST"])
@jwt_required()
def chat_message():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        user_message = data.get("message", "").strip()
        loc = data.get("location") or {}
        lat = loc.get("lat")
        lon = loc.get("lon")

        if not user_message:
            return jsonify({"success": False, "reply": "❌ Please type a message!"}), 400

        env_data = None
        if lat is not None and lon is not None:
            env_data = get_env_data(lat, lon)

        reply = get_gemini_response(user_message, env_data)

        return jsonify(
            {
                "success": True,
                "reply": reply,
                "user_id": user_id,
            }
        ), 200

    except Exception as e:
        logger.error(f"Chatbot endpoint error: {e}")
        return jsonify({"success": False, "reply": "❌ Something went wrong on the server."}), 500


@chatbot_bp.route("/health", methods=["GET"])
def chatbot_health():
    return jsonify(
        {
            "status": "healthy",
            "sdk": "google-genai 1.56.0",
            "model": "gemini-2.5-flash",
        }
    ), 200
