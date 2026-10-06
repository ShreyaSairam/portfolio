"""
WanderWise live services: weather (Open-Meteo), distance, and the Gemini chat.

Open-Meteo is free and needs no API key. Gemini needs a GOOGLE_API_KEY,
read from Streamlit secrets or the environment. Every call has a short
timeout and a fallback, so the app keeps working offline.
"""

import json
import math
import os
import urllib.parse
import urllib.request

# WMO weather codes used by Open-Meteo, grouped into plain words.
WEATHER_WORDS = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow",
    75: "Heavy snow", 80: "Showers", 81: "Showers", 82: "Heavy showers",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
}

# Starting points for people who don't share their location.
CITIES = {
    "Melbourne": (-37.81, 144.96), "Sydney": (-33.87, 151.21), "Chennai": (13.08, 80.27),
    "Mumbai": (19.08, 72.88), "Bengaluru": (12.97, 77.59), "Delhi": (28.61, 77.21),
    "Singapore": (1.35, 103.82), "London": (51.51, -0.13), "New York": (40.71, -74.01),
}


def get_weather(lat, lon, timeout=5):
    """Current conditions plus a 3-day outlook, or None if unreachable."""
    params = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "forecast_days": 3, "timezone": "auto",
    })
    try:
        with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{params}", timeout=timeout) as r:
            data = json.load(r)
    except Exception:
        return None
    cur, daily = data["current"], data["daily"]
    return {
        "temp": cur["temperature_2m"],
        "feels": cur["apparent_temperature"],
        "humidity": cur["relative_humidity_2m"],
        "wind": cur["wind_speed_10m"],
        "summary": WEATHER_WORDS.get(cur["weather_code"], "Mixed"),
        "days": [
            {
                "date": daily["time"][i],
                "max": daily["temperature_2m_max"][i],
                "min": daily["temperature_2m_min"][i],
                "summary": WEATHER_WORDS.get(daily["weather_code"][i], "Mixed"),
                "rain": daily["precipitation_probability_max"][i],
            }
            for i in range(len(daily["time"]))
        ],
    }


def distance_km(a, b):
    """Great-circle (haversine) distance between two (lat, lon) points."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def flight_hours(km):
    """Rough flying time: 800 km/h cruise plus 45 minutes for take-off and landing."""
    return km / 800 + 0.75


def gemini_key():
    try:
        import streamlit as st
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GOOGLE_API_KEY")


def trip_context(dest, weather, origin_name, km):
    lines = [
        f"Destination: {dest['name']}, {dest['country']} ({dest['region']}).",
        f"Climate: {dest['climate']}.",
        f"Best time to visit: {dest['best_season']}.",
        f"Known for: {dest['activities'].replace('|', ', ')}.",
        f"Typical daily cost: about USD {dest['avg_daily_cost_usd']}.",
        f"Distance from {origin_name}: about {km:,.0f} km (roughly {flight_hours(km):.0f} hours flying).",
    ]
    if weather:
        lines.append(
            f"Weather right now: {weather['temp']:.0f}°C, {weather['summary'].lower()}. "
            + "Next days: "
            + "; ".join(f"{d['date']}: {d['min']:.0f} to {d['max']:.0f}°C, {d['summary'].lower()}" for d in weather["days"])
        )
    return "\n".join(lines)


def ask_gemini(question, context, history):
    """Returns (answer, live). live is False when the offline fallback answered."""
    key = gemini_key()
    if key:
        try:
            from google import genai

            client = genai.Client(api_key=key)
            convo = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
            prompt = (
                "You are WanderWise, a friendly, concise travel assistant. Answer in under 120 words, "
                "using the trip facts below and general travel knowledge. If the facts don't cover "
                "something, say what to check.\n\n"
                f"Trip facts:\n{context}\n\nConversation so far:\n{convo}\n\nTraveller: {question}"
            )
            # "gemini-flash-latest" always points at Google's current Flash model.
            for model in (os.environ.get("GEMINI_MODEL"), "gemini-flash-latest", "gemini-2.5-flash"):
                if not model:
                    continue
                try:
                    resp = client.models.generate_content(model=model, contents=prompt)
                    return resp.text.strip(), True
                except Exception:
                    continue
        except Exception:
            pass
    return offline_answer(question, context), False


def offline_answer(question, context):
    """Answers common questions from the trip facts, without an AI model."""
    q = question.lower()
    facts = dict(line.split(": ", 1) for line in context.splitlines() if ": " in line)
    picks = []
    if any(w in q for w in ("weather", "rain", "hot", "cold", "temperature", "pack", "wear")):
        now = facts.get("Weather right now")
        picks.append(f"Right now: {now.strip()}" if now else "Live weather isn't available right now.")
        picks.append(f"Best time to visit: {facts.get('Best time to visit', 'unknown')}")
    if any(w in q for w in ("cost", "budget", "expensive", "cheap", "money", "price")):
        picks.append(f"Typical daily cost: {facts.get('Typical daily cost', 'unknown')}")
    if any(w in q for w in ("far", "fly", "flight", "distance", "get there", "hours")):
        dist = next((v for k, v in facts.items() if k.startswith("Distance from")), "unknown")
        picks.append(f"Distance: {dist}")
    if any(w in q for w in ("do", "see", "activity", "activities", "things", "visit")):
        picks.append(f"It's known for {facts.get('Known for', 'lots to do')}")
    if not picks:
        picks = [facts.get("Destination", ""), f"It's known for {facts.get('Known for', '')}",
                 f"Best time to visit: {facts.get('Best time to visit', '')}"]
    return " ".join(p if p.endswith(".") else p + "." for p in picks if p)
