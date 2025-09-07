from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import base64
import os
import sqlite3
from datetime import datetime
import re
import random

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'farmassist_hackathon_2025'

# Constants
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'demo_key')
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5"

# Pest detection database (simplified for demo)
PEST_DATABASE = {
    "aphids": {
        "name_hi": "माहू/एफिड्स",
        "treatment_hi": "नीम का तेल स्प्रे करें या साबुन के पानी का छिड़काव करें",
    },
    "bollworm": {
        "name_hi": "सुंडी/बॉलवर्म", 
        "treatment_hi": "BT स्प्रे या प्राकृतिक कीटनाशक का प्रयोग करें",
    },
    "leaf_blight": {
        "name_hi": "पत्ती झुलसा रोग",
        "treatment_hi": "कॉपर सल्फेट का छिड़काव करें और पानी कम दें",
    },
    "powdery_mildew": {
        "name_hi": "चूर्णिल आसिता",
        "treatment_hi": "बेकिंग सोडा का घोल या सल्फर पाउडर का प्रयोग करें",
    }
}

# Distress keywords
DISTRESS_KEYWORDS = ["निराश", "आत्महत्या", "कर्ज", "असफल", "suicide", "hopeless", "debt", "failure"]

# Market prices (demo data)
MARKET_PRICES = {
    "wheat": {"price": 2150, "change": 3.2},
    "rice": {"price": 1890, "change": -1.5},
    "cotton": {"price": 5650, "change": 2.8},
}

def detect_distress(message):
    """Simple distress detection"""
    message_lower = message.lower()
    for keyword in DISTRESS_KEYWORDS:
        if keyword in message_lower:
            return True
    return False

def get_weather_data(lat, lon):
    """Fetch weather from OpenWeatherMap"""
    try:
        if OPENWEATHER_API_KEY == 'demo_key':
            # Return demo data if no real API key
            return {
                "main": {"temp": 32, "humidity": 65},
                "weather": [{"description": "clear sky"}]
            }
        
        url = f"{WEATHER_API_URL}/weather"
        params = {
            "lat": lat, "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        response = requests.get(url, params=params, timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return {
            "main": {"temp": 32, "humidity": 65},
            "weather": [{"description": "clear sky"}]
        }

@app.route('/')
def home():
    return jsonify({"message": "FarmAssist API is running!", "version": "1.0"})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        language = data.get('language', 'hi')
        location = data.get('location', '28.6139,77.2090')
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        
        # Check for distress
        is_distressed = detect_distress(message)
        
        # Generate response
        response = generate_response(message, language, location, is_distressed)
        
        return jsonify({
            "reply": response,
            "is_alert": is_distressed,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_response(message, language, location, is_distressed):
    message_lower = message.lower()
    
    # Handle distress
    if is_distressed:
        return """मैं समझ सकता हूं कि यह मुश्किल समय है। 

📞 तुरंत मदद:
• किसान हेल्पलाइन: 1800-180-1551  
• मानसिक स्वास्थ्य: 1800-599-0019

💡 याद रखें: हर समस्या का हल है।"""
    
    # Weather queries
    if any(word in message_lower for word in ["weather", "मौसम", "rain", "बारिश"]):
        lat, lon = map(float, location.split(','))
        weather = get_weather_data(lat, lon)
        temp = weather['main']['temp']
        humidity = weather['main']['humidity']
        
        return f"🌤️ मौसम:\n• तापमान: {temp}°C\n• नमी: {humidity}%\n\n💡 सलाह: तापमान {temp}°C है। {'सिंचाई करें' if temp > 30 else 'सामान्य देखभाल करें'}।"
    
    # Market prices
    elif any(word in message_lower for word in ["price", "दाम", "भाव", "wheat", "गेहूं"]):
        crop = "wheat"
        price_data = MARKET_PRICES[crop]
        change = f"↑{price_data['change']}%" if price_data['change'] > 0 else f"↓{abs(price_data['change'])}%"
        
        return f"💰 आज का भाव:\nगेहूं: ₹{price_data['price']}/क्विंटल\nकल से: {change}\n\n📈 अच्छा भाव है!"
    
    # Pest detection
    elif any(word in message_lower for word in ["pest", "कीट", "disease", "बीमारी"]):
        return "🔍 कीट की पहचान के लिए:\n\n1️⃣ पौधे की तस्वीर खींचें\n2️⃣ कैमरा बटन दबाएं\n3️⃣ अपलोड करें\n\nमैं तुरंत उपचार बताऊंगा!"
    
    # Default response
    else:
        return """नमस्ते! मैं FarmAssist हूं। मैं मदद कर सकता हूं:

🌤️ मौसम की जानकारी
💰 बाज़ार के दाम  
🔍 कीट-रोग की पहचान
🌱 फसल की सलाह
📞 आपातकालीन मदद

आपका सवाल क्या है?"""

@app.route('/api/detect_pest', methods=['POST'])
def detect_pest():
    try:
        data = request.json
        image_data = data.get('image', '')
        
        # Simulate pest detection
        pest_types = list(PEST_DATABASE.keys())
        detected_pest = random.choice(pest_types)
        pest_info = PEST_DATABASE[detected_pest]
        
        return jsonify({
            "pest_name": pest_info['name_hi'],
            "treatment": pest_info['treatment_hi'], 
            "confidence": 0.85
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/weather_alert', methods=['GET'])
def weather_alert():
    try:
        lat = float(request.args.get('lat', 28.6139))
        lon = float(request.args.get('lon', 77.2090))
        
        weather = get_weather_data(lat, lon)
        temp = weather['main']['temp']
        
        if temp > 35:
            alert = f"🌡️ तेज़ गर्मी ({temp}°C)! अधिक पानी दें।"
        elif temp < 10:
            alert = f"🥶 ठंड ({temp}°C)! पाले से बचाएं।"
        else:
            alert = f"🌤️ मौसम सामान्य ({temp}°C)। नियमित देखभाल करें।"
            
        return jsonify({"alert": alert})
    except Exception as e:
        return jsonify({"alert": "मौसम की जानकारी उपलब्ध नहीं है।"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
