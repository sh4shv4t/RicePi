"""Read live system stats from /proc and /sys."""

from __future__ import annotations

import os
import platform
from pathlib import Path


def _read_os_pretty_name() -> str:
    os_release = Path("/etc/os-release")
    if os_release.is_file():
        for line in os_release.read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                value = line.split("=", 1)[1].strip().strip('"')
                return value
    return platform.system()


def _read_uptime() -> str:
    uptime_path = Path("/proc/uptime")
    if not uptime_path.is_file():
        return "unknown"
    seconds = float(uptime_path.read_text(encoding="utf-8").split()[0])
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _read_ram() -> dict[str, int | float]:
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        return {"used_mb": 0, "total_mb": 0, "percent": 0.0}

    values: dict[str, int] = {}
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        values[key.strip()] = int(raw.strip().split()[0])

    total_kb = values.get("MemTotal", 0)
    available_kb = values.get("MemAvailable", values.get("MemFree", 0))
    used_kb = max(total_kb - available_kb, 0)
    total_mb = total_kb // 1024
    used_mb = used_kb // 1024
    percent = round((used_mb / total_mb) * 100, 1) if total_mb else 0.0
    return {"used_mb": used_mb, "total_mb": total_mb, "percent": percent}


def _read_cpu_temp() -> float | None:
    thermal = Path("/sys/class/thermal/thermal_zone0/temp")
    if not thermal.is_file():
        return None
    try:
        return round(int(thermal.read_text(encoding="utf-8").strip()) / 1000.0, 1)
    except (OSError, ValueError):
        return None


def get_sysinfo(items: list[str] | None = None) -> dict:
    requested = items or ["os", "kernel", "uptime", "ram", "cpu_temp"]
    data: dict = {}

    if "os" in requested:
        data["os"] = _read_os_pretty_name()
    if "kernel" in requested:
        data["kernel"] = platform.release()
    if "uptime" in requested:
        data["uptime"] = _read_uptime()
    if "ram" in requested:
        data["ram"] = _read_ram()
    if "cpu_temp" in requested:
        data["cpu_temp"] = _read_cpu_temp()

    return data
