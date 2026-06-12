"""Read live system stats from /proc, /sys, or Windows APIs."""

from __future__ import annotations

import platform
import shutil
import socket
import subprocess
import time
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"


def _format_duration(seconds: float) -> str:
    seconds = max(int(seconds), 0)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _read_os_pretty_name() -> str:
    if IS_WINDOWS:
        release = platform.release()
        return f"Windows {release}" if release else "Windows"
    os_release = Path("/etc/os-release")
    if os_release.is_file():
        for line in os_release.read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    return platform.system()


def _read_kernel() -> str:
    if IS_WINDOWS:
        return platform.release() or "unknown"
    return platform.release()


def _read_cpu_usage() -> float | None:
    if IS_WINDOWS:
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode != 0:
                return None
            value = float(result.stdout.strip())
            return round(value, 1)
        except (OSError, subprocess.SubprocessError, ValueError):
            return None
    return None


def _read_uptime() -> str:
    if IS_WINDOWS:
        try:
            import ctypes

            tick = ctypes.windll.kernel32.GetTickCount64() / 1000.0
            return _format_duration(tick)
        except (OSError, AttributeError):
            return "unknown"
    uptime_path = Path("/proc/uptime")
    if not uptime_path.is_file():
        return "unknown"
    seconds = float(uptime_path.read_text(encoding="utf-8").split()[0])
    return _format_duration(seconds)


def _read_ram() -> dict[str, int | float]:
    if IS_WINDOWS:
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                raise OSError("GlobalMemoryStatusEx failed")
            total_mb = int(stat.ullTotalPhys // (1024 * 1024))
            used_mb = int((stat.ullTotalPhys - stat.ullAvailPhys) // (1024 * 1024))
            percent = round(stat.dwMemoryLoad, 1)
            return {"used_mb": used_mb, "total_mb": total_mb, "percent": percent}
        except OSError:
            return {"used_mb": 0, "total_mb": 0, "percent": 0.0}

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
    if IS_WINDOWS:
        return None
    thermal = Path("/sys/class/thermal/thermal_zone0/temp")
    if not thermal.is_file():
        return None
    try:
        return round(int(thermal.read_text(encoding="utf-8").strip()) / 1000.0, 1)
    except (OSError, ValueError):
        return None


def _read_hostname() -> str:
    try:
        return socket.gethostname().split(".")[0]
    except OSError:
        return "unknown"


def _read_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "offline"


def _read_disk() -> dict[str, int | float]:
    try:
        usage = shutil.disk_usage(Path.cwd().anchor or "/")
        total_gb = round(usage.total / (1024 ** 3), 1)
        used_gb = round((usage.total - usage.free) / (1024 ** 3), 1)
        percent = round((used_gb / total_gb) * 100, 1) if total_gb else 0.0
        return {"used_gb": used_gb, "total_gb": total_gb, "percent": percent}
    except OSError:
        return {"used_gb": 0, "total_gb": 0, "percent": 0.0}


def _read_load_avg() -> str | None:
    if IS_WINDOWS:
        return None
    load_path = Path("/proc/loadavg")
    if not load_path.is_file():
        return None
    parts = load_path.read_text(encoding="utf-8").split()
    if len(parts) >= 3:
        return f"{parts[0]} {parts[1]} {parts[2]}"
    return None


def get_sysinfo(items: list[str] | None = None) -> dict:
    requested = items or ["os", "kernel", "uptime", "ram", "cpu_temp"]
    data: dict = {"platform": platform.system().lower()}

    if "os" in requested:
        data["os"] = _read_os_pretty_name()
    if "kernel" in requested:
        data["kernel"] = _read_kernel()
    if "uptime" in requested:
        data["uptime"] = _read_uptime()
    if "ram" in requested:
        data["ram"] = _read_ram()
    if "cpu_temp" in requested:
        data["cpu_temp"] = _read_cpu_temp()
        if data["cpu_temp"] is None:
            data["cpu_usage"] = _read_cpu_usage()
    if "hostname" in requested:
        data["hostname"] = _read_hostname()
    if "local_ip" in requested:
        data["local_ip"] = _read_local_ip()
    if "disk" in requested:
        data["disk"] = _read_disk()
    if "load_avg" in requested:
        data["load_avg"] = _read_load_avg()

    data["timestamp"] = int(time.time())
    return data
