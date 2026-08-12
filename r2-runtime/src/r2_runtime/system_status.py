"""Privacy-safe Linux and R2 status snapshots for the operator dashboard."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import time
from typing import Mapping


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def _command(*args: str) -> str | None:
    try:
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _memory() -> dict[str, int | float | None]:
    values: dict[str, int] = {}
    text = _read_text(Path("/proc/meminfo"))
    if text:
        for line in text.splitlines():
            name, _, raw = line.partition(":")
            token = raw.strip().split()[0]
            if token.isdigit():
                values[name] = int(token) * 1024
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    used_percent = None
    if total and available is not None:
        used_percent = round((total - available) * 100 / total, 1)
    return {
        "total_bytes": total,
        "available_bytes": available,
        "used_percent": used_percent,
    }


def _network_interfaces() -> dict[str, str]:
    root = Path("/sys/class/net")
    if not root.is_dir():
        return {}
    return {
        path.name: _read_text(path / "operstate") or "unknown" for path in sorted(root.iterdir())
    }


def _service_state(name: str) -> str:
    return _command("systemctl", "is-active", name) or "unknown"


def _os_name() -> str:
    try:
        return platform.freedesktop_os_release().get("PRETTY_NAME", platform.system())
    except OSError:
        return platform.platform()


def collect_system_status() -> dict[str, object]:
    """Collect documented host state without inferring ambient or droid temperature."""

    memory = _memory()
    disk = shutil.disk_usage("/")
    cpu_temp_raw = _read_text(Path("/sys/class/thermal/thermal_zone0/temp"))
    cpu_temp_c = round(float(cpu_temp_raw) / 1000, 3) if cpu_temp_raw else None
    load = os.getloadavg() if hasattr(os, "getloadavg") else (None, None, None)
    uptime_raw = _read_text(Path("/proc/uptime"))
    uptime_s = round(float(uptime_raw.split()[0]), 3) if uptime_raw else None
    throttled = _command("vcgencmd", "get_throttled")
    time_sync = _command("timedatectl", "show", "-p", "NTPSynchronized", "--value")
    status: dict[str, object] = {
        "schema_version": "1.0",
        "measured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "monotonic_ns": time.monotonic_ns(),
        "clock": {
            "clock_id": f"{socket.gethostname()}-monotonic-boot",
            "sync_source": "ntp" if time_sync == "yes" else "unknown",
            "synchronized": time_sync == "yes",
            "uncertainty_ms": None,
        },
        "pi": {
            "hostname": socket.gethostname(),
            "os": _os_name(),
            "kernel": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "uptime_s": uptime_s,
            "load": {"one_min": load[0], "five_min": load[1], "fifteen_min": load[2]},
            "cpu_count": os.cpu_count(),
            "cpu_temperature_c": cpu_temp_c,
            "ambient_temperature_c": None,
            "ambient_temperature_status": "sensor_not_configured",
            "throttling": throttled or "unavailable",
            "memory": memory,
            "disk": {
                "total_bytes": disk.total,
                "free_bytes": disk.free,
                "used_percent": round(disk.used * 100 / disk.total, 1),
            },
            "network_interfaces": _network_interfaces(),
            "services": {
                "apache2": _service_state("apache2"),
                "bluetooth": _service_state("bluetooth"),
                "r2_dashboard_status": _service_state("r2-dashboard-status.service"),
            },
            "audio_cards": _read_text(Path("/proc/asound/cards")) or "unavailable",
            "collector_process": {"pid": os.getpid(), "state": "running"},
        },
    }
    status["issues"] = assess_system_status(status)
    status["overall"] = "attention" if status["issues"] else "nominal"
    return status


def assess_system_status(status: Mapping[str, object]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    pi = status.get("pi")
    clock = status.get("clock")
    if not isinstance(pi, Mapping):
        return [{"severity": "critical", "code": "pi_state_missing", "message": "Pi state missing"}]
    temperature = pi.get("cpu_temperature_c")
    if isinstance(temperature, (int, float)) and temperature >= 80:
        issues.append(
            {"severity": "critical", "code": "pi_cpu_hot", "message": "Pi CPU is at or above 80 C"}
        )
    elif isinstance(temperature, (int, float)) and temperature >= 70:
        issues.append(
            {"severity": "warning", "code": "pi_cpu_warm", "message": "Pi CPU is at or above 70 C"}
        )
    if pi.get("throttling") not in {"throttled=0x0", "unavailable"}:
        issues.append(
            {"severity": "warning", "code": "pi_throttled", "message": "Pi reports a throttle flag"}
        )
    memory = pi.get("memory")
    if isinstance(memory, Mapping):
        total, available = memory.get("total_bytes"), memory.get("available_bytes")
        if isinstance(total, int) and isinstance(available, int) and available < total * 0.1:
            issues.append(
                {
                    "severity": "warning",
                    "code": "memory_low",
                    "message": "Less than 10% memory is available",
                }
            )
    disk = pi.get("disk")
    if isinstance(disk, Mapping) and isinstance(disk.get("used_percent"), (int, float)):
        if float(disk["used_percent"]) >= 90:
            issues.append(
                {
                    "severity": "warning",
                    "code": "disk_low",
                    "message": "Root disk is at least 90% used",
                }
            )
    services = pi.get("services")
    if isinstance(services, Mapping) and services.get("apache2") not in {"active", "unknown"}:
        issues.append(
            {"severity": "warning", "code": "apache_inactive", "message": "Apache is not active"}
        )
    if isinstance(clock, Mapping) and clock.get("synchronized") is False:
        issues.append(
            {
                "severity": "warning",
                "code": "clock_unsynchronized",
                "message": "NTP synchronization is not confirmed",
            }
        )
    return issues


def merge_droid_snapshot(
    system_status: Mapping[str, object], droid_status: Mapping[str, object] | None
) -> dict[str, object]:
    merged = dict(system_status)
    merged["droid"] = dict(droid_status or {"connection": "offline", "status": "unobserved"})
    raw_issues = merged.get("issues", [])
    issues: list[dict[str, str]] = (
        [dict(item) for item in raw_issues if isinstance(item, Mapping)]
        if isinstance(raw_issues, list)
        else []
    )
    if droid_status is None:
        issues.append(
            {
                "severity": "info",
                "code": "droid_status_unobserved",
                "message": "No current droid status snapshot is available",
            }
        )
    else:
        expression = droid_status.get("expression")
        if isinstance(expression, Mapping) and expression.get("status") == "failed":
            issues.append(
                {
                    "severity": "critical",
                    "code": "droid_expression_failed",
                    "message": "The latest R2 expression failed",
                }
            )
        battery = droid_status.get("battery")
        if isinstance(battery, Mapping) and str(battery.get("state", "unknown")).lower() in {
            "low",
            "critical",
            "unknown",
        }:
            issues.append(
                {
                    "severity": "critical",
                    "code": "droid_battery_unsafe",
                    "message": "R2 battery state blocks optional actions",
                }
            )
        if droid_status.get("safe_hold") is False:
            issues.append(
                {
                    "severity": "critical",
                    "code": "droid_safe_hold_unconfirmed",
                    "message": "R2 safe-hold state is not confirmed",
                }
            )
    merged["issues"] = issues
    merged["overall"] = (
        "attention" if any(i.get("severity") != "info" for i in issues) else "nominal"
    )
    return merged
