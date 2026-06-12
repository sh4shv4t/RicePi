"""Network throughput from /proc/net/dev (Linux) with spark history."""

from __future__ import annotations

import platform
import subprocess
import time
from collections import deque
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"
_prev_bytes: tuple[float, int, int] | None = None
_spark_rx: deque[float] = deque(maxlen=12)
_spark_tx: deque[float] = deque(maxlen=12)


def _read_linux_bytes() -> tuple[int, int] | None:
    net_path = Path("/proc/net/dev")
    if not net_path.is_file():
        return None

    rx_total = 0
    tx_total = 0
    for line in net_path.read_text(encoding="utf-8").splitlines()[2:]:
        if ":" not in line:
            continue
        name, stats = line.split(":", 1)
        iface = name.strip()
        if iface == "lo":
            continue
        parts = stats.split()
        if len(parts) < 9:
            continue
        rx_total += int(parts[0])
        tx_total += int(parts[8])
    return rx_total, tx_total


def _read_windows_bytes() -> tuple[int, int] | None:
    script = (
        "$n = Get-NetAdapterStatistics | Where-Object { $_.Name -notlike '*Loopback*' -and $_.Name -notlike '*vEthernet*' }; "
        "$rx = ($n | Measure-Object ReceivedBytes -Sum).Sum; "
        "$tx = ($n | Measure-Object SentBytes -Sum).Sum; "
        "Write-Output \"$rx $tx\""
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            return None
        parts = result.stdout.strip().split()
        if len(parts) < 2:
            return None
        return int(parts[0]), int(parts[1])
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def sample_network() -> dict:
    global _prev_bytes

    if IS_WINDOWS:
        current = _read_windows_bytes()
    else:
        current = _read_linux_bytes()

    if current is None:
        return {
            "available": False,
            "rx_kbps": 0.0,
            "tx_kbps": 0.0,
            "spark_rx": list(_spark_rx),
            "spark_tx": list(_spark_tx),
        }

    now = time.time()
    rx_kbps = 0.0
    tx_kbps = 0.0

    if _prev_bytes is not None:
        prev_time, prev_rx, prev_tx = _prev_bytes
        elapsed = max(now - prev_time, 0.001)
        rx_kbps = max((current[0] - prev_rx) / elapsed / 1024, 0.0)
        tx_kbps = max((current[1] - prev_tx) / elapsed / 1024, 0.0)
        _spark_rx.append(round(rx_kbps, 1))
        _spark_tx.append(round(tx_kbps, 1))

    _prev_bytes = (now, current[0], current[1])

    return {
        "available": True,
        "rx_kbps": round(rx_kbps, 1),
        "tx_kbps": round(tx_kbps, 1),
        "spark_rx": list(_spark_rx),
        "spark_tx": list(_spark_tx),
    }


def get_network() -> dict:
    return sample_network()
