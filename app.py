import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/api/weather_alert")
def weather_alert():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat and lon required"}), 400

    # Basic OpenWeatherMap current weather call
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return jsonify({"error": "failed to fetch weather", "details": r.text}), 500

    data = r.json()
    weather_desc = data.get("weather", [{}])[0].get("description", "")
    temp = data.get("main", {}).get("temp")

    advisory = f"Current: {weather_desc}, {temp}°C. "
    if "rain" in weather_desc.lower():
        advisory += "Rain likely — protect harvested crops; delay irrigation."
    elif temp is not None and temp >= 35:
        advisory += "Very hot — irrigate early morning/evening."
    else:
        advisory += "Conditions normal."

    return jsonify({"weather": data, "advisory": advisory})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
