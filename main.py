"""RicePi FastAPI server."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import init_theme
import sysinfo as sysinfo_module
from scheduler import start_scheduler

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
STATIC_DIR = ROOT / "static"
DATA_DIR = ROOT / "data"

_scheduler = None


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def enrich_config(config: dict) -> dict:
    enriched = json.loads(json.dumps(config))
    anim_folder = ROOT / config.get("animation", {}).get("folder", "static/animations/")
    if anim_folder.is_dir():
        files = sorted(
            p.name
            for p in anim_folder.iterdir()
            if p.suffix.lower() in {".gif", ".webm", ".mp4"}
        )
        enriched.setdefault("animation", {})["available"] = files
    else:
        enriched.setdefault("animation", {})["available"] = []
    return enriched


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    init_theme.generate_theme()
    _scheduler = start_scheduler()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


app = FastAPI(title="RicePi", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/theme.css")
async def theme_css():
    return FileResponse(ROOT / "theme.css", media_type="text/css")


@app.get("/api/config")
async def get_config():
    return enrich_config(load_config())


@app.post("/api/reload")
async def reload_config():
    config = load_config()
    init_theme.generate_theme()
    return {"status": "ok", "config": enrich_config(config)}


@app.get("/api/weather")
async def get_weather():
    cache_path = DATA_DIR / "weather_cache.json"
    if not cache_path.is_file():
        return JSONResponse({"error": "no cache"}, status_code=404)
    with cache_path.open(encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/sysinfo")
async def get_sysinfo():
    config = load_config()
    items = config.get("sysinfo", {}).get("items", [])
    return sysinfo_module.get_sysinfo(items)


@app.get("/api/quotes")
async def get_quotes():
    quotes_path = DATA_DIR / "quotes.json"
    with quotes_path.open(encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/events")
async def get_events():
    events_path = DATA_DIR / "events.json"
    with events_path.open(encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import uvicorn

    init_theme.generate_theme()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
