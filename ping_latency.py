"""ICMP ping latency via system ping command."""

from __future__ import annotations

import platform
import re
import subprocess

DEFAULT_HOST = "8.8.8.8"
IS_WINDOWS = platform.system() == "Windows"


def ping_host(host: str = DEFAULT_HOST, timeout_ms: int = 1000) -> dict:
    if IS_WINDOWS:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
    else:
        timeout_sec = max(int(timeout_ms / 1000), 1)
        cmd = ["ping", "-c", "1", "-W", str(timeout_sec), host]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(timeout_ms / 1000 + 2, 3),
            check=False,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            return {"host": host, "ms": None, "ok": False}

        if IS_WINDOWS:
            match = re.search(r"(?:time[<=]|time=)(\d+(?:\.\d+)?)\s*ms", output, re.I)
        else:
            match = re.search(r"time=(\d+(?:\.\d+)?)\s*ms", output)

        if not match:
            return {"host": host, "ms": None, "ok": False}

        return {"host": host, "ms": round(float(match.group(1)), 1), "ok": True}
    except (OSError, subprocess.SubprocessError, ValueError):
        return {"host": host, "ms": None, "ok": False}
