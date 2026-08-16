from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from enum import IntEnum
from queue import SimpleQueue
from types import SimpleNamespace
import unittest

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.encounters import StationaryExpressionPlan
from r2_runtime.spherov2_backend import (
    HardwareActionNotAuthorized,
    Spherov2LibraryBackend,
    StationaryProbePolicy,
    StationaryExpressionError,
    TracedRawMotorOffExecutor,
    ResilientBleakAdapter,
)
from r2_runtime.packet_trace import StopResponseTraceRecorder, classify_stop_response_trace
from r2_runtime.session_recording import SessionClock


class Version:
    def __init__(self, major: int, minor: int, revision: int) -> None:
        self.major = major
        self.minor = minor
        self.revision = revision


class FakeLeds(IntEnum):
    LOGIC_DISPLAYS = 3


class FakeRawMotorModes(IntEnum):
    OFF = 0
    FORWARD = 1


class FakeAudio(IntEnum):
    R2_HEY_1 = 2813


class FakeLedControl:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls

    def set_leds(self, mapping: dict[FakeLeds, int]) -> None:
        self.calls.append(("leds", dict(mapping)))


class FakeDriveControl:
    def __init__(self, calls: list[object]) -> None:
        self.calls = calls

    def set_raw_motors(
        self,
        left_mode: FakeRawMotorModes,
        left_speed: int,
        right_mode: FakeRawMotorModes,
        right_speed: int,
    ) -> None:
        self.calls.append(("raw_motors", left_mode, left_speed, right_mode, right_speed))


class FakeToy:
    name = "D2-TEST"
    address = "private-address-must-not-escape"
    LEDs = FakeLeds
    Audio = FakeAudio
    sensors = OrderedDict((name, object()) for name in ("quaternion", "locator"))
    extended_sensors = OrderedDict((name, object()) for name in ("r2_head_angle", "gyroscope"))

    def __init__(self) -> None:
        self.calls: list[object] = []
        self.drive_control = FakeDriveControl(self.calls)
        self.multi_led_control = FakeLedControl(self.calls)
        self._Toy__packet_queue: SimpleQueue[bytes] = SimpleQueue()

    def __enter__(self) -> "FakeToy":
        self.calls.append("enter")
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.calls.append("exit")

    def get_three_character_sku(self) -> bytes:
        return b"D2A"

    def get_main_app_version(self) -> Version:
        return Version(1, 2, 3)

    def get_bootloader_version(self) -> Version:
        return Version(4, 5, 6)

    def get_board_revision(self) -> int:
        return 7

    def get_processor_name(self) -> bytes:
        return b"R2-MCU"

    def get_battery_voltage_state(self) -> object:
        return SimpleNamespace(name="OK")

    def get_battery_voltage(self) -> float:
        return 3.81

    def get_head_position(self) -> float:
        self.calls.append("head_read")
        return 0.0

    def set_head_position(self, position: float) -> None:
        self.calls.append(("head_set", position))

    def get_audio_volume(self) -> int:
        self.calls.append("audio_get_volume")
        return 40

    def wake(self) -> None:
        self.calls.append("wake")

    def set_audio_volume(self, volume: int) -> None:
        self.calls.append(("audio_volume", volume))

    def play_audio_file(self, audio_id: int, mode: int) -> None:
        self.calls.append(("audio_play", audio_id, mode))

    def stop_all_audio(self) -> None:
        self.calls.append("audio_stop")

    def configure_collision_detection(self) -> None:
        raise AssertionError("inspection must not configure collision detection")


class FakePacket:
    def __init__(self, *, flags: int, did: int, cid: int, seq: int, err: object = None) -> None:
        self.flags = flags
        self.did = did
        self.cid = cid
        self.seq = seq
        self.err = err

    def build(self) -> bytes:
        return bytes((self.flags, self.did, self.cid, self.seq))


class FakeDriveCommand:
    encoded_data: list[object] = []

    @staticmethod
    def _encode(toy: object, cid: int, proc: object, data: list[object]) -> FakePacket:
        FakeDriveCommand.encoded_data = list(data)
        return FakePacket(flags=10, did=22, cid=cid, seq=17)


class FakeExecutingToy(FakeToy):
    def _execute(self, packet: FakePacket) -> FakePacket:
        self.calls.append(("execute", packet.did, packet.cid, packet.seq))
        return FakePacket(
            flags=1,
            did=packet.did,
            cid=packet.cid,
            seq=packet.seq,
            err=SimpleNamespace(name="success"),
        )


class FakeScanner:
    def __init__(self, toy: FakeToy) -> None:
        self.toy = toy
        self.arguments: dict[str, object] = {}

    def find_toy(self, **kwargs: object) -> FakeToy:
        self.arguments = kwargs
        return self.toy

    def find_toys(self, **kwargs: object) -> list[object]:
        self.arguments = kwargs
        return []


class Spherov2BackendTest(unittest.TestCase):
    def make_backend(
        self, policy: StationaryProbePolicy | None = None
    ) -> tuple[Spherov2LibraryBackend, FakeToy, FakeScanner, type]:
        toy = FakeToy()
        scanner = FakeScanner(toy)
        r2_type = type("R2D2", (), {})
        modules = {
            "spherov2.scanner": scanner,
            "spherov2.toy.r2d2": SimpleNamespace(R2D2=r2_type),
            "spherov2.controls": SimpleNamespace(RawMotorModes=FakeRawMotorModes),
            "spherov2.commands.drive": SimpleNamespace(
                Drive=FakeDriveCommand, RawMotorModes=FakeRawMotorModes
            ),
        }
        backend = Spherov2LibraryBackend(
            policy=policy,
            module_loader=lambda name: modules[name],  # type: ignore[arg-type]
            version_resolver=lambda _: "0.12.1",
        )
        return backend, toy, scanner, r2_type

    def test_exact_identity_and_r2_type_filter_are_used(self) -> None:
        backend, toy, scanner, r2_type = self.make_backend()
        backend.connect("D2-TEST")
        self.assertEqual(scanner.arguments["toy_name"], "D2-TEST")
        self.assertEqual(scanner.arguments["toy_types"], (r2_type,))
        self.assertEqual(scanner.arguments["timeout"], 5.0)
        self.assertEqual(toy.calls, ["enter"])
        backend.disconnect()
        self.assertEqual(toy.calls[-1], "exit")

    def test_identity_excludes_private_ble_address_and_mac_query(self) -> None:
        backend, _, _, _ = self.make_backend()
        backend.connect("D2-TEST")
        identity = backend.identity()
        self.assertNotIn("address", identity)
        self.assertNotIn("private-address", str(identity))
        self.assertEqual(identity["firmware"], "1.2.3")
        self.assertEqual(identity["system"], "D2A")
        backend.disconnect()

    def test_emergency_stop_is_queued_without_execute_or_response_wait(self) -> None:
        backend, toy, _, _ = self.make_backend()
        backend.connect("D2-TEST")
        backend.dispatch_stop_no_wait()
        self.assertEqual(toy._Toy__packet_queue.get_nowait(), bytes((10, 22, 1, 17)))
        self.assertEqual(FakeDriveCommand.encoded_data, [0, 0, 0, 0])
        self.assertFalse(
            any(isinstance(call, tuple) and call[0] == "execute" for call in toy.calls)
        )
        backend.disconnect()

    def test_bounded_forward_is_queued_without_execute_or_response_wait(self) -> None:
        backend, toy, _, _ = self.make_backend()
        backend.connect("D2-TEST")
        backend.dispatch_bounded_forward_no_wait(5)
        self.assertEqual(toy._Toy__packet_queue.get_nowait(), bytes((10, 22, 1, 17)))
        self.assertEqual(FakeDriveCommand.encoded_data, [1, 5, 1, 5])
        self.assertFalse(
            any(isinstance(call, tuple) and call[0] == "execute" for call in toy.calls)
        )
        with self.assertRaises(ValueError):
            backend.dispatch_bounded_forward_no_wait(11)
        backend.disconnect()

    def test_default_policy_denies_stationary_actuation(self) -> None:
        backend, toy, _, _ = self.make_backend()
        backend.connect("D2-TEST")
        before = list(toy.calls)
        for capability in ("led.low_brightness", "head.safe_range", "audio.quiet_preview"):
            with (
                self.subTest(capability=capability),
                self.assertRaises(HardwareActionNotAuthorized),
            ):
                backend.exercise_stationary(capability)
        self.assertEqual(toy.calls, before)
        backend.disconnect()

    def test_wake_on_connect_is_separately_authorized_and_default_off(self) -> None:
        backend, toy, _, _ = self.make_backend()
        backend.connect("D2-TEST")
        self.assertNotIn("wake", toy.calls)
        backend.disconnect()

        policy = StationaryProbePolicy(allow_wake_on_connect=True)
        backend, toy, _, _ = self.make_backend(policy)
        backend.connect("D2-TEST")
        self.assertEqual(toy.calls[:2], ["enter", "wake"])
        backend.disconnect()

    def test_authorized_previews_restore_led_and_audio_state(self) -> None:
        policy = StationaryProbePolicy(
            allow_led_preview=True,
            allow_head_read=True,
            allow_audio_preview=True,
            audio_id=1704,
            audio_volume=8,
        )
        backend, toy, _, _ = self.make_backend(policy)
        backend.connect("D2-TEST")
        backend.exercise_stationary("led.low_brightness")
        backend.exercise_stationary("head.safe_range")
        backend.exercise_stationary("audio.quiet_preview")
        self.assertIn(("leds", {FakeLeds.LOGIC_DISPLAYS: 0}), toy.calls)
        self.assertIn("head_read", toy.calls)
        self.assertEqual(
            toy.calls[-4:],
            [("audio_volume", 8), ("audio_play", 1704, 0), "audio_stop", ("audio_volume", 40)],
        )
        backend.disconnect()

    def test_led_preview_has_bounded_visible_dwell(self) -> None:
        policy = StationaryProbePolicy(allow_led_preview=True, led_preview_dwell_s=1.25)
        backend, toy, _, _ = self.make_backend(policy)
        dwells: list[float] = []
        backend._sleeper = dwells.append
        backend.connect("D2-TEST")
        result = backend.exercise_stationary("led.low_brightness")
        self.assertEqual(dwells, [1.25])
        self.assertEqual(result["restored"], True)
        self.assertEqual(
            [call for call in toy.calls if isinstance(call, tuple) and call[0] == "leds"],
            [("leds", {FakeLeds.LOGIC_DISPLAYS: 8}), ("leds", {FakeLeds.LOGIC_DISPLAYS: 0})],
        )
        backend.disconnect()

    def test_audio_preview_reports_empty_volume_response_phase(self) -> None:
        policy = StationaryProbePolicy(allow_audio_preview=True, audio_id=1704)
        backend, toy, _, _ = self.make_backend(policy)
        backend.connect("D2-TEST")
        toy.get_audio_volume = lambda: (_ for _ in ()).throw(IndexError())  # type: ignore[method-assign]
        with self.assertRaises(StationaryExpressionError) as caught:
            backend.exercise_stationary("audio.quiet_preview")
        self.assertEqual(caught.exception.phase, "audio_volume_read")
        self.assertEqual(caught.exception.error_type, "IndexError")
        self.assertNotIn("audio_stop", toy.calls)
        backend.disconnect()

    def test_stationary_expression_uses_only_head_audio_and_led_then_restores(self) -> None:
        policy = StationaryProbePolicy(
            allow_stationary_expressions=True,
            allowed_audio_names=frozenset({"R2_HEY_1"}),
        )
        backend, toy, _, _ = self.make_backend(policy)
        backend._sleeper = lambda _: None
        backend.connect("D2-TEST")
        plan = StationaryExpressionPlan("greeting", "R2_HEY_1", (0.0, -16.0, 16.0, 0.0))
        backend.perform_stationary_expression(plan)
        self.assertFalse(
            any(call[0] == "raw_motors" for call in toy.calls if isinstance(call, tuple))
        )
        self.assertIn(("audio_play", FakeAudio.R2_HEY_1, 0), toy.calls)
        self.assertEqual(
            [call for call in toy.calls if isinstance(call, tuple) and call[0] == "leds"][:5],
            [
                ("leds", {FakeLeds.LOGIC_DISPLAYS: 0}),
                ("leds", {FakeLeds.LOGIC_DISPLAYS: 8}),
                ("leds", {FakeLeds.LOGIC_DISPLAYS: 0}),
                ("leds", {FakeLeds.LOGIC_DISPLAYS: 8}),
                ("leds", {FakeLeds.LOGIC_DISPLAYS: 0}),
            ],
        )
        self.assertEqual(
            toy.calls[-2:], [("head_set", 0.0), ("leds", {FakeLeds.LOGIC_DISPLAYS: 0})]
        )
        backend.disconnect()

    def test_stationary_expression_is_default_denied(self) -> None:
        backend, _, _, _ = self.make_backend()
        backend.connect("D2-TEST")
        plan = StationaryExpressionPlan("greeting", "R2_HEY_1", (0.0,))
        with self.assertRaises(HardwareActionNotAuthorized):
            backend.perform_stationary_expression(plan)
        backend.disconnect()

    def test_expression_eof_preserves_phase_restores_and_skips_futile_stop(self) -> None:
        policy = StationaryProbePolicy(
            allow_stationary_expressions=True,
            allowed_audio_names=frozenset({"R2_HEY_1"}),
        )
        backend, toy, _, _ = self.make_backend(policy)
        toy.get_audio_volume = lambda: (_ for _ in ()).throw(EOFError())  # type: ignore[method-assign]
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-TEST")
        owner = BleOwner(driver)
        owner.connect_for_stationary_probe()
        plan = StationaryExpressionPlan("greeting", "R2_HEY_1", (0.0,))
        with self.assertRaises(StationaryExpressionError) as caught:
            owner.perform_stationary_expression(plan)
        self.assertEqual(caught.exception.phase, "audio_volume_read")
        self.assertEqual(caught.exception.error_type, "EOFError")
        self.assertTrue(driver.transport_failed)
        self.assertIn("audio_stop", toy.calls)
        self.assertIn(("head_set", 0.0), toy.calls)
        self.assertIn(("leds", {FakeLeds.LOGIC_DISPLAYS: 0}), toy.calls)
        owner.disconnect("expression_transport_failed")
        self.assertFalse(
            any(call[0] == "raw_motors" for call in toy.calls if isinstance(call, tuple))
        )
        self.assertEqual(toy.calls[-1], "exit")
        self.assertFalse(driver.transport_failed)

    def test_nearby_scan_returns_only_types_and_excludes_configured_r2(self) -> None:
        class R2Type(FakeToy):
            pass

        class R2Q5Type:
            pass

        class BB8Type:
            def __init__(self) -> None:
                self.name = "private-bb8-name"

        class BB9EType:
            pass

        own_r2 = R2Type()
        own_r2.name = "configured-private-r2"
        bb8 = BB8Type()
        scanner = FakeScanner(own_r2)
        scanner.find_toys = lambda **kwargs: [own_r2, bb8]  # type: ignore[method-assign]
        modules = {
            "spherov2.scanner": scanner,
            "spherov2.toy.r2d2": SimpleNamespace(R2D2=R2Type),
            "spherov2.toy.r2q5": SimpleNamespace(R2Q5=R2Q5Type),
            "spherov2.toy.bb8": SimpleNamespace(BB8=BB8Type),
            "spherov2.toy.bb9e": SimpleNamespace(BB9E=BB9EType),
        }
        backend = Spherov2LibraryBackend(
            module_loader=lambda name: modules[name],  # type: ignore[arg-type]
            version_resolver=lambda _: "0.12.1",
        )
        observed = backend.discover_nearby_droids("configured-private-r2")
        self.assertEqual(observed, ("bb8",))
        self.assertNotIn("private", str(observed))

    def test_owner_disconnect_dispatches_raw_motor_off_before_close(self) -> None:
        backend, toy, _, _ = self.make_backend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-TEST")
        owner = BleOwner(driver)
        owner.connect_for_stationary_probe()
        owner.disconnect("test")
        self.assertEqual(
            toy.calls[-2:],
            [("raw_motors", FakeRawMotorModes.OFF, 0, FakeRawMotorModes.OFF, 0), "exit"],
        )
        self.assertTrue(owner.stopped)

    def test_read_only_capability_inventory_does_not_start_streaming(self) -> None:
        backend, toy, _, _ = self.make_backend()
        backend.connect("D2-TEST")
        telemetry = backend.exercise_stationary("telemetry.stationary")
        collision = backend.exercise_stationary("collision.configuration")
        self.assertEqual(
            telemetry["streams"], ("gyroscope", "locator", "quaternion", "r2_head_angle")
        )
        self.assertTrue(collision["configuration_supported"])
        self.assertEqual(toy.calls, ["enter"])
        backend.disconnect()

    def test_bench_executor_observes_exact_vendor_command_without_changing_flags(self) -> None:
        recorder = StopResponseTraceRecorder(
            session_ref="session-0123456789abcdef",
            clock=SessionClock("sim-clock-abcdef01", "deterministic", 0.0),
            utc_now=lambda: datetime(2030, 1, 1, tzinfo=timezone.utc),
            monotonic_ns=iter((1000, 2000)).__next__,
        )
        toy = FakeExecutingToy()
        scanner = FakeScanner(toy)
        modules = {
            "spherov2.scanner": scanner,
            "spherov2.toy.r2d2": SimpleNamespace(R2D2=type("R2D2", (), {})),
            "spherov2.commands.drive": SimpleNamespace(
                Drive=FakeDriveCommand, RawMotorModes=FakeRawMotorModes
            ),
        }
        backend = Spherov2LibraryBackend(
            module_loader=lambda name: modules[name],  # type: ignore[arg-type]
            version_resolver=lambda _: "0.12.1",
            stop_executor=TracedRawMotorOffExecutor(recorder),
        )
        backend.connect("D2-TEST")
        backend.stop()
        backend.disconnect()
        self.assertEqual(
            FakeDriveCommand.encoded_data, [FakeRawMotorModes.OFF, 0, FakeRawMotorModes.OFF, 0]
        )
        self.assertIn(("execute", 22, 1, 17), toy.calls)
        payload = recorder.finalize(
            owner_state="offline", ble_connections=0, physical_state="normal"
        )
        self.assertEqual(classify_stop_response_trace(payload), "acknowledged_success")
        self.assertEqual(payload["observations"][0]["flags"], 10)

    def test_resilient_adapter_closes_worker_after_already_disconnected_eof(self) -> None:
        class Device:
            is_connected = False

            def disconnect(self) -> object:
                return object()

        class EventLoop:
            closed = False
            stopped = False

            def call_soon_threadsafe(self, callback: object) -> None:
                self.stopped = True

            def stop(self) -> None:
                self.stopped = True

            def is_closed(self) -> bool:
                return self.closed

            def close(self) -> None:
                self.closed = True

        class Thread:
            joined = False

            def join(self, timeout: float) -> None:
                self.joined = timeout == 2.0

            def is_alive(self) -> bool:
                return False

        delegate = SimpleNamespace(
            _BleakAdapter__device=Device(),
            _BleakAdapter__event_loop=EventLoop(),
            _BleakAdapter__thread=Thread(),
            _BleakAdapter__execute=lambda _value: (_ for _ in ()).throw(EOFError()),
        )
        adapter = ResilientBleakAdapter.__new__(ResilientBleakAdapter)
        adapter._delegate = delegate
        adapter.close()
        self.assertTrue(delegate._BleakAdapter__event_loop.stopped)
        self.assertTrue(delegate._BleakAdapter__event_loop.closed)
        self.assertTrue(delegate._BleakAdapter__thread.joined)


if __name__ == "__main__":
    unittest.main()
