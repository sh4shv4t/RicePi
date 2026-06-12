"""Background jobs: weather, ping, network, spotify."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from apscheduler.schedulers.background import BackgroundScheduler

import network as network_module
import ping_latency
import spotify as spotify_module

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
WEATHER_CACHE_PATH = ROOT / "data" / "weather_cache.json"
PING_CACHE_PATH = ROOT / "data" / "ping_cache.json"
NETWORK_CACHE_PATH = ROOT / "data" / "network_cache.json"

WMO_MAP = {
    0: "sunny",
    1: "partly_cloudy",
    2: "partly_cloudy",
    3: "cloudy",
    45: "fog",
    48: "fog",
    51: "rain",
    53: "rain",
    55: "rain",
    56: "rain",
    57: "rain",
    61: "rain",
    63: "rain",
    65: "rain",
    66: "rain",
    67: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    80: "rain",
    81: "rain",
    82: "rain",
    85: "snow",
    86: "snow",
    95: "thunderstorm",
    96: "thunderstorm",
    99: "thunderstorm",
}


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _write_cache(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def map_weather_code(code: int, is_day: bool = True, wind_speed: float = 0.0) -> str:
    if wind_speed >= 30 and code in (0, 1, 2, 3):
        return "windy"
    if code == 0 and not is_day:
        return "night_clear"
    return WMO_MAP.get(code, "cloudy")


def _format_sun_time(iso_value: str | None) -> str | None:
    if not iso_value:
        return None
    try:
        dt = datetime.fromisoformat(iso_value)
        return dt.strftime("%H:%M")
    except ValueError:
        return iso_value.split("T")[-1][:5] if "T" in iso_value else iso_value


def fetch_weather() -> dict:
    config = load_config()
    location = config.get("location", {})
    lat = location.get("lat", 0)
    lon = location.get("lon", 0)
    city = location.get("city", "Unknown")
    units = config.get("weather", {}).get("units", "metric")

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weathercode,windspeed_10m,is_day",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,sunrise,sunset",
        "timezone": "auto",
    }
    if units == "imperial":
        params["temperature_unit"] = "fahrenheit"
        params["windspeed_unit"] = "mph"
    else:
        params["temperature_unit"] = "celsius"
        params["windspeed_unit"] = "kmh"

    url = "https://api.open-meteo.com/v1/forecast"
    with httpx.Client(timeout=20.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    current = payload.get("current", {})
    daily = payload.get("daily", {})
    current_code = int(current.get("weathercode", 0))
    is_day = bool(current.get("is_day", 1))
    wind_speed = float(current.get("windspeed_10m", 0))

    daily_codes = daily.get("weathercode", [])
    daily_max = daily.get("temperature_2m_max", [])
    daily_min = daily.get("temperature_2m_min", [])
    daily_sunrise = daily.get("sunrise", [])
    daily_sunset = daily.get("sunset", [])

    sunrise = _format_sun_time(daily_sunrise[0] if daily_sunrise else None)
    sunset = _format_sun_time(daily_sunset[0] if daily_sunset else None)

    forecast_today = []
    if daily_codes:
        forecast_today.append(
            {
                "code": int(daily_codes[0]),
                "condition": map_weather_code(int(daily_codes[0]), is_day=True, wind_speed=wind_speed),
                "max": daily_max[0] if daily_max else None,
                "min": daily_min[0] if daily_min else None,
                "sunrise": sunrise,
                "sunset": sunset,
            }
        )

    cache = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "city": city,
        "units": units,
        "sunrise": sunrise,
        "sunset": sunset,
        "current": {
            "temperature": current.get("temperature_2m"),
            "weathercode": current_code,
            "condition": map_weather_code(current_code, is_day=is_day, wind_speed=wind_speed),
            "windspeed": wind_speed,
            "is_day": is_day,
        },
        "today": forecast_today,
    }

    _write_cache(WEATHER_CACHE_PATH, cache)
    return cache


def fetch_ping() -> dict:
    config = load_config()
    host = config.get("status", {}).get("ping_host", "8.8.8.8")
    result = ping_latency.ping_host(host)
    result["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_cache(PING_CACHE_PATH, result)
    return result


def sample_network() -> dict:
    result = network_module.sample_network()
    result["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_cache(NETWORK_CACHE_PATH, result)
    return result


def fetch_spotify() -> dict:
    return spotify_module.fetch_now_playing()


def ensure_weather_cache() -> None:
    if not WEATHER_CACHE_PATH.is_file():
        try:
            fetch_weather()
        except Exception as exc:
            fallback = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "city": "Unknown",
                "units": "metric",
                "sunrise": None,
                "sunset": None,
                "current": {
                    "temperature": None,
                    "weathercode": 0,
                    "condition": "sunny",
                    "windspeed": 0,
                    "is_day": True,
                },
                "today": [],
                "error": str(exc),
            }
            _write_cache(WEATHER_CACHE_PATH, fallback)


def start_scheduler() -> BackgroundScheduler:
    config = load_config()
    weather_mins = config.get("weather", {}).get("update_interval_mins", 15)
    ping_secs = config.get("status", {}).get("ping_interval_secs", 30)
    network_secs = config.get("status", {}).get("network_interval_secs", 2)
    spotify_secs = config.get("spotify", {}).get("poll_secs", 10)

    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_weather, "interval", minutes=weather_mins, id="weather_fetch")
    scheduler.add_job(fetch_ping, "interval", seconds=ping_secs, id="ping_fetch")
    scheduler.add_job(sample_network, "interval", seconds=network_secs, id="network_sample")

    if config.get("spotify", {}).get("enabled"):
        scheduler.add_job(fetch_spotify, "interval", seconds=spotify_secs, id="spotify_fetch")

    scheduler.start()

    ensure_weather_cache()
    try:
        fetch_weather()
    except Exception as exc:
        print(f"[scheduler] Initial weather fetch failed: {exc}")

    try:
        fetch_ping()
    except Exception as exc:
        print(f"[scheduler] Initial ping failed: {exc}")

    sample_network()

    if config.get("spotify", {}).get("enabled"):
        try:
            fetch_spotify()
        except Exception as exc:
            print(f"[scheduler] Initial spotify fetch failed: {exc}")

    return scheduler
