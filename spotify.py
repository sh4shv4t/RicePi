"""Now-playing via playerctl, Spotify Web API, Windows media session, or local URL."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
CACHE_PATH = ROOT / "data" / "spotify_cache.json"
ART_CACHE_PATH = ROOT / "data" / "spotify_art.jpg"
WINDOWS_MEDIA_SCRIPT = ROOT / "scripts" / "windows_media.ps1"

IS_WINDOWS = platform.system() == "Windows"
_token_cache: dict = {"access_token": None, "expires_at": 0.0}
_last_track_key: str | None = None


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _empty() -> dict:
    return {
        "playing": False,
        "artist": None,
        "title": None,
        "source": None,
        "has_art": False,
    }


def _track_key(artist: str | None, title: str | None) -> str:
    return f"{artist or ''}::{title or ''}"


def _clear_art() -> None:
    if ART_CACHE_PATH.is_file():
        ART_CACHE_PATH.unlink(missing_ok=True)


def _save_art_bytes(content: bytes) -> bool:
    if not content:
        return False
    ART_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ART_CACHE_PATH.write_bytes(content)
    return True


def _save_art_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme == "file":
        local_path = Path(unquote(parsed.path))
        if local_path.is_file():
            return _save_art_bytes(local_path.read_bytes())
        return False
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return _save_art_bytes(response.content)
    except httpx.HTTPError:
        return False


def _playerctl_art(target: str | None) -> None:
    if not shutil.which("playerctl"):
        return
    for key in ("mpris:artUrl", "xesam:artUrl"):
        cmd = ["playerctl", "metadata", key]
        if target:
            cmd = ["playerctl", "-p", target, "metadata", key]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3, check=False)
            url = result.stdout.strip()
            if result.returncode == 0 and url:
                _save_art_url(url)
                return
        except (OSError, subprocess.SubprocessError):
            continue


def _fetch_art_lookup(artist: str | None, title: str | None) -> bool:
    if not artist and not title:
        return False
    query = " ".join(part for part in (artist, title) if part)
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://itunes.apple.com/search",
                params={"term": query, "entity": "song", "limit": 1},
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                return False
            art_url = results[0].get("artworkUrl100", "").replace("100x100bb", "600x600bb")
            if not art_url:
                art_url = results[0].get("artworkUrl100", "").replace("100x100", "600x600")
            return _save_art_url(art_url) if art_url else False
    except httpx.HTTPError:
        return False


def _attach_art(data: dict, *, player: str | None = None, art_url: str | None = None) -> dict:
    global _last_track_key

    if not data.get("playing"):
        _last_track_key = None
        _clear_art()
        data["has_art"] = False
        return data

    key = _track_key(data.get("artist"), data.get("title"))
    if key != _last_track_key:
        _last_track_key = key
        saved = False
        if art_url:
            saved = _save_art_url(art_url)
        elif data.get("source") == "playerctl":
            _playerctl_art(player)
            saved = ART_CACHE_PATH.is_file()
        if not saved:
            _fetch_art_lookup(data.get("artist"), data.get("title"))

    data["has_art"] = ART_CACHE_PATH.is_file()
    if data["has_art"]:
        data["art_url"] = f"/api/spotify/art?t={int(time.time())}"
    return data


def _playerctl(player: str | None = "spotify") -> dict:
    if not shutil.which("playerctl"):
        return {**_empty(), "error": "playerctl not found"}

    players = [player] if player else []
    players.append(None)

    for target in players:
        try:
            status_cmd = ["playerctl"]
            meta_cmd = ["playerctl"]
            if target:
                status_cmd.extend(["-p", target])
                meta_cmd.extend(["-p", target])
            status_cmd.append("status")
            meta_cmd.extend(["metadata", "--format", "{{artist}}|||{{title}}"])

            status = subprocess.run(
                status_cmd,
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            if status.returncode != 0 or status.stdout.strip().lower() != "playing":
                continue

            meta = subprocess.run(
                meta_cmd,
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            if meta.returncode != 0:
                continue

            parts = meta.stdout.strip().split("|||", 1)
            artist = parts[0].strip() if parts else None
            title = parts[1].strip() if len(parts) > 1 else None
            if not title:
                continue

            data = {
                "playing": True,
                "artist": artist or None,
                "title": title,
                "source": "playerctl",
            }
            return _attach_art(data, player=target)
        except (OSError, subprocess.SubprocessError):
            continue

    return _empty()


def _windows_media() -> dict:
    if not WINDOWS_MEDIA_SCRIPT.is_file():
        return {**_empty(), "error": "windows media script missing"}

    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(WINDOWS_MEDIA_SCRIPT),
            "-ArtOut",
            str(ART_CACHE_PATH),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        if result.returncode != 0:
            return {**_empty(), "error": result.stderr.strip() or "windows media failed"}

        payload = json.loads(result.stdout.strip() or "{}")
        if not payload.get("playing"):
            return _empty()

        data = {
            "playing": True,
            "artist": payload.get("artist"),
            "title": payload.get("title"),
            "source": "windows_media",
        }
        return _attach_art(data)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return {**_empty(), "error": str(exc)}


def _refresh_web_token(web_cfg: dict) -> str | None:
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 30:
        return _token_cache["access_token"]

    client_id = web_cfg.get("client_id", "")
    client_secret = web_cfg.get("client_secret", "")
    refresh_token = web_cfg.get("refresh_token", "")
    if not all([client_id, client_secret, refresh_token]):
        return None

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
            response.raise_for_status()
            payload = response.json()
            _token_cache["access_token"] = payload["access_token"]
            _token_cache["expires_at"] = now + payload.get("expires_in", 3600)
            return _token_cache["access_token"]
    except (httpx.HTTPError, KeyError):
        return None


def _web_api(web_cfg: dict) -> dict:
    token = _refresh_web_token(web_cfg)
    if not token:
        return {**_empty(), "error": "spotify auth failed"}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://api.spotify.com/v1/me/player/currently-playing",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 204:
                return _empty()
            response.raise_for_status()
            payload = response.json()

        if not payload.get("item"):
            return _empty()

        item = payload["item"]
        artists = ", ".join(a["name"] for a in item.get("artists", []))
        images = item.get("album", {}).get("images", [])
        art_url = images[0]["url"] if images else None
        data = {
            "playing": payload.get("is_playing", True),
            "artist": artists or None,
            "title": item.get("name"),
            "source": "web_api",
        }
        return _attach_art(data, art_url=art_url)
    except httpx.HTTPError:
        return _empty()


def _local_poll(url: str) -> dict:
    if not url:
        return {**_empty(), "error": "local_url not set"}
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
        data = {
            "playing": bool(payload.get("playing", payload.get("title"))),
            "artist": payload.get("artist"),
            "title": payload.get("title"),
            "source": "local",
        }
        return _attach_art(data, art_url=payload.get("art_url") or payload.get("artUrl"))
    except (httpx.HTTPError, json.JSONDecodeError, KeyError):
        return _empty()


def _web_api_configured(spotify_cfg: dict) -> bool:
    web_cfg = spotify_cfg.get("web_api", {})
    return all(web_cfg.get(key) for key in ("client_id", "client_secret", "refresh_token"))


def _resolve_auto(spotify_cfg: dict) -> dict:
    if IS_WINDOWS:
        result = _windows_media()
        if result.get("playing"):
            return result

    player = spotify_cfg.get("playerctl_player", "spotify")
    result = _playerctl(player)
    if result.get("playing"):
        return result

    if _web_api_configured(spotify_cfg):
        return _web_api(spotify_cfg.get("web_api", {}))

    local_url = spotify_cfg.get("local_url", "")
    if local_url:
        return _local_poll(local_url)

    return _empty()


def fetch_now_playing() -> dict:
    config = load_config()
    spotify_cfg = config.get("spotify", {})
    if not spotify_cfg.get("enabled", False):
        _clear_art()
        return _empty()

    source = spotify_cfg.get("source", "auto")
    if source == "auto":
        data = _resolve_auto(spotify_cfg)
    elif source == "playerctl":
        data = _playerctl(spotify_cfg.get("playerctl_player", "spotify"))
    elif source == "windows_media":
        data = _windows_media()
    elif source == "web_api":
        data = _web_api(spotify_cfg.get("web_api", {}))
    elif source == "local":
        data = _local_poll(spotify_cfg.get("local_url", ""))
    else:
        data = {**_empty(), "error": f"unknown source: {source}"}

    if not data.get("playing"):
        _clear_art()
        data["has_art"] = False

    data["updated_at"] = time.time()
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def get_art_path() -> Path | None:
    if ART_CACHE_PATH.is_file():
        return ART_CACHE_PATH
    return None


def get_cached_now_playing() -> dict:
    if CACHE_PATH.is_file():
        with CACHE_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        if data.get("playing") and ART_CACHE_PATH.is_file():
            data["has_art"] = True
            data["art_url"] = f"/api/spotify/art?t={int(time.time())}"
        return data
    return fetch_now_playing()
