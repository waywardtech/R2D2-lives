"""Reviewed, lazy-loaded adapter for spherov2 0.12.1.

This module imports no third-party package at import time and exposes no raw
spherov2 objects. Construction and unit tests cannot scan or connect to BLE.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module, metadata
import time
from types import ModuleType
from typing import Any, Callable, Mapping, Protocol

from .encounters import StationaryExpressionPlan
from .packet_trace import StopResponseTraceRecorder


class HardwareActionNotAuthorized(PermissionError):
    pass


class StationaryExpressionError(RuntimeError):
    """Sanitized expression failure retaining only a stable phase and exception type."""

    def __init__(self, phase: str, error_type: str) -> None:
        super().__init__(f"stationary expression failed during {phase}")
        self.phase = phase
        self.error_type = error_type


class StopExecutor(Protocol):
    def __call__(self, toy: Any, module_loader: Callable[[str], ModuleType]) -> None: ...


def _public_raw_motor_off(toy: Any, module_loader: Callable[[str], ModuleType]) -> None:
    controls = module_loader("spherov2.controls")
    off = controls.RawMotorModes.OFF
    toy.drive_control.set_raw_motors(off, 0, off, 0)


class TracedRawMotorOffExecutor:
    """Bench-only observer over the pinned private encode/execute seam."""

    def __init__(self, recorder: StopResponseTraceRecorder) -> None:
        self.recorder = recorder

    def __call__(self, toy: Any, module_loader: Callable[[str], ModuleType]) -> None:
        drive = module_loader("spherov2.commands.drive")
        off = drive.RawMotorModes.OFF
        packet = drive.Drive._encode(toy, 1, None, [off, 0, off, 0])
        self.recorder.record(
            direction="tx",
            did=int(packet.did),
            cid=int(packet.cid),
            protocol_sequence=int(packet.seq),
            flags=int(packet.flags),
            encoded_packet=bytes(packet.build()),
        )
        response = toy._execute(packet)
        error = getattr(response.err, "name", str(response.err)).lower()
        self.recorder.record(
            direction="rx",
            did=int(response.did),
            cid=int(response.cid),
            protocol_sequence=int(response.seq),
            flags=int(response.flags),
            encoded_packet=bytes(response.build()),
            error=error,
        )


@dataclass(frozen=True)
class StationaryProbePolicy:
    allow_led_preview: bool = False
    allow_head_read: bool = False
    allow_audio_preview: bool = False
    audio_id: int | None = None
    audio_volume: int = 8
    allow_stationary_expressions: bool = False
    allowed_audio_names: frozenset[str] = frozenset()

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
        stop_executor: StopExecutor = _public_raw_motor_off,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if not 0 < scan_timeout_s <= 30:
            raise ValueError("scan timeout must be in (0, 30] seconds")
        self.policy = policy or StationaryProbePolicy()
        self.scan_timeout_s = scan_timeout_s
        self._module_loader = module_loader
        self._version_resolver = version_resolver
        self._stop_executor = stop_executor
        self._sleeper = sleeper
        # The third-party package is deliberately absent from the simulation
        # environment, so its dynamic object is confined to this adapter boundary.
        self._toy: Any | None = None

    @property
    def library_version(self) -> str:
        return self._version_resolver("spherov2")

    def _require_toy(self) -> Any:
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

    def discover_nearby_droids(self, configured_identity: str) -> tuple[str, ...]:
        if self._toy is not None:
            raise RuntimeError("nearby-droid scan requires an offline R2 connection")
        scanner = self._module_loader("spherov2.scanner")
        modules_and_names = (
            ("spherov2.toy.r2d2", "R2D2", "r2d2"),
            ("spherov2.toy.r2q5", "R2Q5", "r2q5"),
            ("spherov2.toy.bb8", "BB8", "bb8"),
            ("spherov2.toy.bb9e", "BB9E", "bb9e"),
        )
        typed_kinds = tuple(
            (getattr(self._module_loader(module_name), class_name), kind)
            for module_name, class_name, kind in modules_and_names
        )
        toys = scanner.find_toys(
            timeout=self.scan_timeout_s,
            toy_types=tuple(toy_type for toy_type, _ in typed_kinds),
        )
        observed: set[str] = set()
        for candidate in toys:
            if getattr(candidate, "name", None) == configured_identity:
                continue
            for toy_type, kind in typed_kinds:
                if isinstance(candidate, toy_type):
                    observed.add(kind)
                    break
        return tuple(sorted(observed))

    def disconnect(self) -> None:
        toy, self._toy = self._toy, None
        if toy is not None:
            toy.__exit__(None, None, None)

    def stop(self) -> None:
        toy = self._require_toy()
        self._stop_executor(toy, self._module_loader)

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
                raise HardwareActionNotAuthorized(
                    "head-position query was not explicitly authorized"
                )
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

    def perform_stationary_expression(self, plan: StationaryExpressionPlan) -> None:
        if not self.policy.allow_stationary_expressions:
            raise HardwareActionNotAuthorized(
                "stationary expressions were not explicitly authorized"
            )
        if plan.audio_name not in self.policy.allowed_audio_names:
            raise HardwareActionNotAuthorized("audio is outside the operator-authorized allowlist")
        toy = self._require_toy()
        if any(abs(position) > 20.0 for position in plan.head_positions_deg):
            raise HardwareActionNotAuthorized("head gesture exceeds the stationary bound")
        audio = getattr(toy.Audio, plan.audio_name, None)
        if audio is None:
            raise RuntimeError("authorized audio enum is unavailable on this R2 adapter")
        logic_display = toy.LEDs.LOGIC_DISPLAYS
        phase = "head_position_read"
        original_head: float | None = None
        original_volume: int | None = None
        failure: tuple[str, Exception] | None = None
        try:
            original_head = float(toy.get_head_position())
            phase = "audio_volume_read"
            original_volume = int(toy.get_audio_volume())
            phase = "logic_display_set"
            toy.multi_led_control.set_leds({logic_display: plan.logic_display_brightness})
            phase = "audio_volume_set"
            toy.set_audio_volume(plan.audio_volume)
            for position in plan.head_positions_deg:
                phase = "head_position_set"
                toy.set_head_position(position)
                self._sleeper(0.2)
            phase = "audio_play"
            toy.play_audio_file(audio, 0)
            self._sleeper(plan.audio_dwell_s)
        except Exception as error:
            failure = (phase, error)

        cleanup: tuple[tuple[str, Callable[[], None]], ...] = (
            ("audio_stop_restore", toy.stop_all_audio),
            (
                "audio_volume_restore",
                lambda: (
                    toy.set_audio_volume(original_volume) if original_volume is not None else None
                ),
            ),
            (
                "head_position_restore",
                lambda: toy.set_head_position(original_head) if original_head is not None else None,
            ),
            ("logic_display_restore", lambda: toy.multi_led_control.set_leds({logic_display: 0})),
        )
        for cleanup_phase, operation in cleanup:
            try:
                operation()
            except Exception as error:
                if failure is None:
                    failure = (cleanup_phase, error)
        if failure is not None:
            failure_phase, original_failure = failure
            raise StationaryExpressionError(
                failure_phase, type(original_failure).__name__
            ) from original_failure
