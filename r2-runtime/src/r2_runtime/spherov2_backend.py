"""Reviewed, lazy-loaded adapter for spherov2 0.12.1.

This module imports no third-party package at import time and exposes no raw
spherov2 objects. Construction and unit tests cannot scan or connect to BLE.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module, metadata
from threading import Event
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


class ResilientBleakAdapter:
    """Pinned-adapter wrapper that cannot strand its non-daemon event-loop thread."""

    @staticmethod
    def _vendor() -> type[Any]:
        module = import_module("spherov2.adapter.bleak_adapter")
        return module.BleakAdapter  # type: ignore[no-any-return]

    @classmethod
    def scan_toys(cls, timeout: float = 5.0) -> Any:
        return cls._vendor().scan_toys(timeout)

    @classmethod
    def scan_toy(cls, name: str, timeout: float = 5.0) -> Any:
        return cls._vendor().scan_toy(name, timeout)

    def __init__(self, address: object) -> None:
        self._delegate = self._vendor()(address)

    def set_callback(self, uuid: str, callback: Callable[..., object]) -> None:
        self._delegate.set_callback(uuid, callback)

    def write(self, uuid: str, data: bytes | bytearray) -> None:
        self._delegate.write(uuid, data)

    def close(self, disconnect: bool = True) -> None:
        adapter = self._delegate
        disconnect_error: Exception | None = None
        try:
            if disconnect:
                adapter._BleakAdapter__execute(adapter._BleakAdapter__device.disconnect())
        except (EOFError, ConnectionError, OSError) as error:
            disconnect_error = error
        finally:
            event_loop = adapter._BleakAdapter__event_loop
            thread = adapter._BleakAdapter__thread
            event_loop.call_soon_threadsafe(event_loop.stop)
            thread.join(timeout=2.0)
            if thread.is_alive():
                raise TimeoutError("BLE adapter event-loop thread did not stop")
            if not event_loop.is_closed():
                event_loop.close()
        if disconnect_error is not None and adapter._BleakAdapter__device.is_connected:
            raise disconnect_error


@dataclass(frozen=True)
class StationaryProbePolicy:
    # R201 wake physically cycles the leg stance; this is not link-only setup.
    # Keep default-off and enable only after explicit bounded stance authorization.
    allow_wake_on_connect: bool = False
    allow_led_preview: bool = False
    led_preview_dwell_s: float = 1.5
    allow_head_read: bool = False
    allow_session_initialized_head_read: bool = False
    allow_passive_telemetry_sample: bool = False
    telemetry_sample_window_s: float = 1.0
    allow_audio_preview: bool = False
    audio_id: int | None = None
    audio_volume: int = 8
    allow_stationary_expressions: bool = False
    allowed_audio_names: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not 0.1 <= self.led_preview_dwell_s <= 2.0:
            raise ValueError("LED preview dwell must be in [0.1, 2.0] seconds")
        if not 0 <= self.audio_volume <= 16:
            raise ValueError("quiet audio preview volume must be in [0, 16]")
        if not 0.1 <= self.telemetry_sample_window_s <= 2.0:
            raise ValueError("telemetry sample window must be in [0.1, 2.0] seconds")
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
            adapter=ResilientBleakAdapter,
        )
        if getattr(toy, "name", None) != configured_identity:
            raise RuntimeError("discovered droid identity did not exactly match configuration")
        toy.__enter__()
        if self.policy.allow_wake_on_connect:
            try:
                toy.wake()
            except Exception:
                toy.__exit__(None, None, None)
                raise
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

    def dispatch_stop_no_wait(self) -> None:
        """Queue raw-motor OFF/0 directly; this deliberately does not await a response."""
        self._queue_raw_motors_no_wait("OFF", 0)

    def dispatch_bounded_forward_no_wait(self, speed: int) -> None:
        """Queue an explicitly bounded low-speed forward command without a response wait."""
        if not 1 <= speed <= 25:
            raise ValueError("bounded raw-motor speed must be in [1, 25]")
        self._queue_raw_motors_no_wait("FORWARD", speed)

    def dispatch_heading_forward_no_wait(self, speed: int, heading_degrees: int = 0) -> None:
        """Queue Drive CID 7 forward heading control without awaiting firmware response."""
        self._queue_heading_forward_no_wait(speed, heading_degrees, secondary=True)

    def dispatch_stock_heading_forward_no_wait(self, speed: int, heading_degrees: int = 0) -> None:
        """Queue the stock R2 Drive CID 7 binding with its default processor."""
        self._queue_heading_forward_no_wait(speed, heading_degrees, secondary=False)

    def _queue_heading_forward_no_wait(
        self, speed: int, heading_degrees: int, *, secondary: bool
    ) -> None:
        if not 1 <= speed <= 25 or not 0 <= heading_degrees <= 359:
            raise ValueError("heading drive bounds are invalid")
        toy = self._require_toy()
        drive = self._module_loader("spherov2.commands.drive")
        processor = None
        if secondary:
            processors = self._module_loader("spherov2.controls.v2")
            processor = processors.Processors.SECONDARY
        packet = drive.Drive._encode(
            toy,
            7,
            processor,
            [speed, heading_degrees >> 8, heading_degrees & 0xFF, drive.DriveFlags.FORWARD],
        )
        queue = getattr(toy, "_Toy__packet_queue", None)
        if queue is None or not hasattr(queue, "put"):
            raise RuntimeError("pinned toy transport queue is unavailable")
        queue.put(packet.build())

    def dispatch_r2_drive_forward_no_wait(self, speed: int) -> None:
        """Queue the R2-specific paired generic-drive motors (Drive CID 11)."""
        if not 1 <= speed <= 25:
            raise ValueError("R2 drive speed must be in [1, 25]")
        toy = self._require_toy()
        drive = self._module_loader("spherov2.commands.drive")
        processors = self._module_loader("spherov2.controls.v2")
        queue = getattr(toy, "_Toy__packet_queue", None)
        if queue is None or not hasattr(queue, "put"):
            raise RuntimeError("pinned toy transport queue is unavailable")
        for index in (
            drive.GenericRawMotorIndexes.LEFT_DRIVE,
            drive.GenericRawMotorIndexes.RIGHT_DRIVE,
        ):
            packet = drive.Drive._encode(
                toy,
                11,
                processors.Processors.SECONDARY,
                [index, drive.GenericRawMotorModes.FORWARD, 0, speed],
            )
            queue.put(packet.build())

    def dispatch_three_legs_no_wait(self) -> None:
        self._queue_leg_action_no_wait("THREE_LEGS")

    def dispatch_two_legs_no_wait(self) -> None:
        """Queue the R2 stance return after a bounded motion diagnostic."""
        self._queue_leg_action_no_wait("TWO_LEGS")

    def _queue_leg_action_no_wait(self, action_name: str) -> None:
        toy = self._require_toy()
        animatronic = self._module_loader("spherov2.commands.animatronic")
        queue = getattr(toy, "_Toy__packet_queue", None)
        if queue is None or not hasattr(queue, "put"):
            raise RuntimeError("pinned toy transport queue is unavailable")
        packet = animatronic.Animatronic._encode(
            toy, 13, None, [getattr(animatronic.R2LegActions, action_name)]
        )
        queue.put(packet.build())

    def _queue_raw_motors_no_wait(self, mode_name: str, speed: int) -> None:
        toy = self._require_toy()
        drive = self._module_loader("spherov2.commands.drive")
        processors = self._module_loader("spherov2.controls.v2")
        mode = getattr(drive.RawMotorModes, mode_name)
        packet = drive.Drive._encode(
            toy, 1, processors.Processors.SECONDARY, [mode, speed, mode, speed]
        )
        queue = getattr(toy, "_Toy__packet_queue", None)
        if queue is None or not hasattr(queue, "put"):
            raise RuntimeError("pinned toy transport queue is unavailable")
        queue.put(packet.build())

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
                self._sleeper(self.policy.led_preview_dwell_s)
            finally:
                toy.multi_led_control.set_leds({led: 0})
            return {"result": "exercised", "brightness": 8, "restored": True}
        if capability == "head.safe_range":
            if not self.policy.allow_head_read:
                raise HardwareActionNotAuthorized(
                    "head-position query was not explicitly authorized"
                )
            return {"result": "read_only", "head_position": float(toy.get_head_position())}
        if capability == "head.session_initialized_read":
            if not self.policy.allow_session_initialized_head_read:
                raise HardwareActionNotAuthorized(
                    "session-initialized head read was not explicitly authorized"
                )
            if not self.policy.allow_wake_on_connect:
                raise HardwareActionNotAuthorized(
                    "session-initialized head read requires explicit wake authorization"
                )
            utilities = self._module_loader("spherov2.utils").ToyUtil
            utilities.set_robot_state_on_start(toy)
            utilities.enable_sensors(
                toy, ["attitude", "accelerometer", "gyroscope", "locator", "velocity"]
            )
            return {
                "result": "read_only",
                "head_position": float(toy.get_head_position()),
                "session_initialized": True,
                "streams": ("accelerometer", "attitude", "gyroscope", "locator", "velocity"),
            }
        if capability == "audio.quiet_preview":
            if not self.policy.allow_audio_preview:
                raise HardwareActionNotAuthorized("audio preview was not explicitly authorized")
            phase = "audio_volume_read"
            previous: int | None = None
            primary_error: Exception | None = None
            try:
                previous = int(toy.get_audio_volume())
                phase = "audio_volume_set"
                toy.set_audio_volume(self.policy.audio_volume)
                phase = "audio_play"
                toy.play_audio_file(self.policy.audio_id, 0)
            except Exception as error:
                primary_error = error
            cleanup_error: Exception | None = None
            if previous is not None:
                for cleanup_phase, cleanup in (
                    ("audio_stop_restore", toy.stop_all_audio),
                    ("audio_volume_restore", lambda: toy.set_audio_volume(previous)),
                ):
                    try:
                        cleanup()
                    except Exception as error:
                        if cleanup_error is None:
                            cleanup_error = StationaryExpressionError(
                                cleanup_phase, type(error).__name__
                            )
            if primary_error is not None:
                raise StationaryExpressionError(
                    phase, type(primary_error).__name__
                ) from primary_error
            if cleanup_error is not None:
                raise cleanup_error
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
        if capability == "telemetry.passive_sample":
            if not self.policy.allow_passive_telemetry_sample:
                raise HardwareActionNotAuthorized(
                    "passive telemetry sampling was not explicitly authorized"
                )
            control = getattr(toy, "sensor_control", None)
            if control is None:
                raise RuntimeError("R201 sensor-control surface is unavailable")
            samples: list[object] = []
            received = Event()

            def listener(sample: object) -> None:
                if len(samples) < 8:
                    samples.append(sample)
                received.set()

            control.add_sensor_data_listener(listener)
            try:
                control.enable("attitude", "accelerometer", "gyroscope", "locator", "velocity")
                received.wait(self.policy.telemetry_sample_window_s)
            finally:
                try:
                    control.disable_all()
                finally:
                    control.remove_sensor_data_listener(listener)
            return {
                "result": "sampled" if samples else "no_sample",
                "sample_count": len(samples),
                "window_s": self.policy.telemetry_sample_window_s,
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
            phase = "logic_display_flash"
            for brightness in plan.logic_display_pattern:
                toy.multi_led_control.set_leds({logic_display: brightness})
                self._sleeper(plan.light_dwell_s)
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
