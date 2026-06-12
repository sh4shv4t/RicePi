"""Aggregate live status: ping, network, spotify."""

from __future__ import annotations

import json
from pathlib import Path

import network as network_module
import ping_latency
import spotify as spotify_module

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def get_status() -> dict:
    config = load_config()
    status_cfg = config.get("status", {})

    ping_host = status_cfg.get("ping_host", "8.8.8.8")
    ping = ping_latency.ping_host(ping_host)

    net = network_module.get_network()

    spotify_cfg = config.get("spotify", {})
    if spotify_cfg.get("enabled"):
        spotify = spotify_module.get_cached_now_playing()
    else:
        spotify = {"playing": False, "artist": None, "title": None}

    return {
        "ping": ping,
        "network": net,
        "spotify": spotify,
    }
