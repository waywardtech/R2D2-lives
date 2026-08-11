"""Reviewed, lazy-loaded adapter for spherov2 0.12.1.

This module imports no third-party package at import time and exposes no raw
spherov2 objects. Construction and unit tests cannot scan or connect to BLE.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module, metadata
from types import ModuleType
from typing import Callable, Mapping


class HardwareActionNotAuthorized(PermissionError):
    pass


@dataclass(frozen=True)
class StationaryProbePolicy:
    allow_led_preview: bool = False
    allow_head_read: bool = False
    allow_audio_preview: bool = False
    audio_id: int | None = None
    audio_volume: int = 8

    def __post_init__(self) -> None:
        if not 0 <= self.audio_volume <= 16:
            raise ValueError("quiet audio preview volume must be in [0, 16]")
        if self.allow_audio_preview and self.audio_id is None:
            raise ValueError("authorized audio preview requires an explicit verified audio ID")


def _installed_version(distribution: str) -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return "unavailable"


def _public_text(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("ascii", errors="replace")
    if hasattr(value, "major") and hasattr(value, "minor") and hasattr(value, "revision"):
        return f"{value.major}.{value.minor}.{value.revision}"
    return str(value)


class Spherov2LibraryBackend:
    """Narrow production adapter; all actual use must remain inside BleOwner."""

    def __init__(
        self,
        *,
        policy: StationaryProbePolicy | None = None,
        scan_timeout_s: float = 5.0,
        module_loader: Callable[[str], ModuleType] = import_module,
        version_resolver: Callable[[str], str] = _installed_version,
    ) -> None:
        if not 0 < scan_timeout_s <= 30:
            raise ValueError("scan timeout must be in (0, 30] seconds")
        self.policy = policy or StationaryProbePolicy()
        self.scan_timeout_s = scan_timeout_s
        self._module_loader = module_loader
        self._version_resolver = version_resolver
        self._toy: object | None = None

    @property
    def library_version(self) -> str:
        return self._version_resolver("spherov2")

    def _require_toy(self) -> object:
        if self._toy is None:
            raise RuntimeError("spherov2 backend is not connected")
        return self._toy

    def connect(self, configured_identity: str) -> None:
        if self._toy is not None:
            raise RuntimeError("spherov2 backend already connected")
        scanner = self._module_loader("spherov2.scanner")
        r2_module = self._module_loader("spherov2.toy.r2d2")
        toy = scanner.find_toy(
            toy_name=configured_identity,
            toy_types=(r2_module.R2D2,),
            timeout=self.scan_timeout_s,
        )
        if getattr(toy, "name", None) != configured_identity:
            raise RuntimeError("discovered droid identity did not exactly match configuration")
        toy.__enter__()
        self._toy = toy

    def disconnect(self) -> None:
        toy, self._toy = self._toy, None
        if toy is not None:
            toy.__exit__(None, None, None)

    def stop(self) -> None:
        toy = self._require_toy()
        controls = self._module_loader("spherov2.controls")
        off = controls.RawMotorModes.OFF
        toy.drive_control.set_raw_motors(off, 0, off, 0)

    def identity(self) -> Mapping[str, str]:
        toy = self._require_toy()
        # Deliberately omit address and get_mac_address().
        return {
            "model": "R2-D2 R201",
            "system": _public_text(toy.get_three_character_sku()),
            "firmware": _public_text(toy.get_main_app_version()),
            "bootloader": _public_text(toy.get_bootloader_version()),
            "board_revision": _public_text(toy.get_board_revision()),
            "processor": _public_text(toy.get_processor_name()),
        }

    def battery(self) -> Mapping[str, object]:
        toy = self._require_toy()
        state = toy.get_battery_voltage_state()
        return {
            "state": getattr(state, "name", str(state)).lower(),
            "voltage_v": float(toy.get_battery_voltage()),
            "provenance": "r201_firmware_query",
        }

    def exercise_stationary(self, capability: str) -> Mapping[str, object]:
        toy = self._require_toy()
        if capability == "led.low_brightness":
            if not self.policy.allow_led_preview:
                raise HardwareActionNotAuthorized("LED preview was not explicitly authorized")
            led = toy.LEDs.LOGIC_DISPLAYS
            try:
                toy.multi_led_control.set_leds({led: 8})
            finally:
                toy.multi_led_control.set_leds({led: 0})
            return {"result": "exercised", "brightness": 8, "restored": True}
        if capability == "head.safe_range":
            if not self.policy.allow_head_read:
                raise HardwareActionNotAuthorized("head-position query was not explicitly authorized")
            return {"result": "read_only", "head_position": float(toy.get_head_position())}
        if capability == "audio.quiet_preview":
            if not self.policy.allow_audio_preview:
                raise HardwareActionNotAuthorized("audio preview was not explicitly authorized")
            previous = int(toy.get_audio_volume())
            try:
                toy.set_audio_volume(self.policy.audio_volume)
                toy.play_audio_file(self.policy.audio_id, 0)
            finally:
                toy.stop_all_audio()
                toy.set_audio_volume(previous)
            return {
                "result": "exercised",
                "audio_id": self.policy.audio_id,
                "volume": self.policy.audio_volume,
                "restored": True,
            }
        if capability == "telemetry.stationary":
            return {
                "result": "advertised_only",
                "streams": tuple(sorted((*toy.sensors.keys(), *toy.extended_sensors.keys()))),
            }
        if capability == "collision.configuration":
            return {
                "result": "advertised_only",
                "configuration_supported": hasattr(toy, "configure_collision_detection"),
            }
        raise ValueError(f"unsupported stationary capability: {capability}")
