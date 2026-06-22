import datetime as dt

import requests
from django.conf import settings


def get_weather_for_day(day) -> dict:
    day_date = day.date
    today = dt.date.today()

    api_key = settings.WEATHER_API_KEY
    if api_key:
        try:
            url = (
                f"{settings.WEATHER_API_BASE_URL}/forecast.json"
                f"?key={api_key}&q={day.trip.destination}"
                f"&dt={day_date.strftime('%Y-%m-%d')}"
            )
            response = requests.get(url, timeout=settings.EXTERNAL_REQUEST_TIMEOUT).json()
            if "forecast" in response:
                day_forecast = response["forecast"]["forecastday"][0]["day"]
                condition = day_forecast.get("condition", {}).get("text", "Sunny")
                avg_temp = day_forecast.get("avgtemp_c", 24.0)
                is_today = day_date == today
                label = (
                    "Live Forecast"
                    if is_today or (day_date - today).days <= 10
                    else "Predicted Climate"
                )
                emoji = (
                    "☀️"
                    if "sun" in condition.lower() or "clear" in condition.lower()
                    else "⛅"
                )
                return {
                    "label": label,
                    "emoji": emoji,
                    "temperature_c": round(float(avg_temp), 1),
                    "condition": condition,
                    "is_demo_data": False,
                }
        except Exception:
            pass

    theme = day.theme.lower()
    avg_temp = 24.0
    condition = "Mild & Pleasant"
    emoji = "⛅"
    if "mountain" in theme or "hike" in theme or "alpine" in theme:
        avg_temp, condition, emoji = 18.0, "Breezy & Cool", "⛰️💨"
    elif "beach" in theme or "coast" in theme or "waterfront" in theme:
        avg_temp, condition, emoji = 30.0, "Warm & Sunny", "🏖️☀️"
    elif "rain" in theme:
        avg_temp, condition, emoji = 20.0, "Showers", "🌧️"

    return {
        "label": "Estimated · Demo data",
        "emoji": emoji,
        "temperature_c": avg_temp,
        "condition": condition,
        "is_demo_data": True,
    }
