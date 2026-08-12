from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from enum import IntEnum
from types import SimpleNamespace
import unittest

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.spherov2_backend import (
    HardwareActionNotAuthorized,
    Spherov2LibraryBackend,
    StationaryProbePolicy,
    TracedRawMotorOffExecutor,
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
    sensors = OrderedDict((name, object()) for name in ("quaternion", "locator"))
    extended_sensors = OrderedDict((name, object()) for name in ("r2_head_angle", "gyroscope"))

    def __init__(self) -> None:
        self.calls: list[object] = []
        self.drive_control = FakeDriveControl(self.calls)
        self.multi_led_control = FakeLedControl(self.calls)

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

    def get_audio_volume(self) -> int:
        self.calls.append("audio_get_volume")
        return 40

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


if __name__ == "__main__":
    unittest.main()
