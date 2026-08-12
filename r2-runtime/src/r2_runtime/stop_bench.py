"""Deterministic orchestration for the separately gated stationary stop bench."""

from __future__ import annotations

from dataclasses import dataclass

from .ble_owner import BleOwner
from .drivers import Spherov2R2Driver


@dataclass(frozen=True)
class StopBenchSessionResult:
    error_type: str | None
    battery_state: str


def run_stop_bench_session(
    owner: BleOwner, driver: Spherov2R2Driver
) -> StopBenchSessionResult:
    """Connect, inspect battery, then issue the owner's one disconnect stop."""

    error_type: str | None = None
    battery_state = "unobserved"
    try:
        owner.connect_for_stationary_probe()
        battery = owner.serialized(driver.backend.battery)
        battery_state = str(battery.get("state", "unknown")).lower()
        if battery_state not in {"ok", "charged", "not_charging"}:
            error_type = "UnsafeBatteryState"
    except Exception as error:
        error_type = type(error).__name__
    finally:
        if driver.connected:
            try:
                owner.disconnect("stationary_probe_complete")
            except Exception as error:
                error_type = error_type or type(error).__name__
    return StopBenchSessionResult(error_type=error_type, battery_state=battery_state)
