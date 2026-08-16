from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from r2_runtime.ble_owner import BleOwner, ConnectionState
from r2_runtime.capability_probe import (
    MOVEMENT_CAPABILITIES,
    CapabilityProbeError,
    StationaryCapabilityProbe,
)
from r2_runtime.drivers import (
    HardwareUnavailableError,
    Spherov2R2Driver,
    UnavailableSpherov2Backend,
)
from r2_runtime.recording import (
    build_hil_failure_evidence,
    read_verified_json,
    write_immutable_json,
)
from r2_runtime.sim_hardware import SimSpherov2Backend


class CapabilityProbeTest(unittest.TestCase):
    def make_probe(
        self,
    ) -> tuple[SimSpherov2Backend, Spherov2R2Driver, BleOwner, StationaryCapabilityProbe]:
        backend = SimSpherov2Backend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver)
        return backend, driver, owner, StationaryCapabilityProbe(owner, driver)

    def test_stationary_probe_records_capabilities_without_movement(self) -> None:
        backend, driver, owner, probe = self.make_probe()
        report = probe.run(generated_at="2030-01-01T00:00:00Z")
        self.assertEqual(report.evidence_category, "simulation")
        self.assertFalse(report.movement_performed)
        self.assertEqual(report.final_state, "safe_hold")
        self.assertTrue(owner.stopped)
        self.assertEqual(owner.state, ConnectionState.OFFLINE)
        for capability in MOVEMENT_CAPABILITIES:
            self.assertEqual(report.capabilities[capability].status, "untested")
        self.assertNotIn("D2-SIMULATED", str(report.to_dict()))
        self.assertNotIn("drive.bounded", backend.calls)

    def test_five_simulated_cycles_end_stopped(self) -> None:
        for _ in range(5):
            backend, _, owner, probe = self.make_probe()
            probe.run(generated_at="2030-01-01T00:00:00Z")
            self.assertTrue(owner.stopped)
            self.assertEqual(backend.calls[-2:], ["stop", "disconnect"])

    def test_link_loss_and_reconnect_do_not_resume(self) -> None:
        backend, driver, owner, _ = self.make_probe()
        owner.connect_for_stationary_probe()
        driver.stopped = False  # injected unsafe/stale local state
        owner.link_lost()
        self.assertTrue(owner.stopped)
        self.assertFalse(driver.connected)
        owner.connect_for_stationary_probe()
        self.assertTrue(owner.stopped)
        self.assertTrue(backend.stopped)
        owner.disconnect("test_complete")

    def test_wrong_library_version_fails_closed(self) -> None:
        backend = SimSpherov2Backend(library_version="0.12.0")
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver)
        with self.assertRaisesRegex(RuntimeError, "expected spherov2.py 0.12.1"):
            owner.connect_for_stationary_probe()
        self.assertTrue(owner.stopped)
        self.assertEqual(owner.state, ConnectionState.OFFLINE)

    def test_partial_connect_failure_attempts_stop_and_disconnect(self) -> None:
        class PartialFailureBackend(SimSpherov2Backend):
            def connect(self, configured_identity: str) -> None:
                self.connected = True
                self.calls.append("connect_partial")
                raise OSError("injected handshake failure")

        backend = PartialFailureBackend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver)
        with self.assertRaisesRegex(OSError, "handshake failure"):
            owner.connect_for_stationary_probe()
        self.assertEqual(backend.calls, ["connect_partial", "stop", "disconnect"])
        self.assertTrue(owner.stopped)
        self.assertFalse(driver.connected)
        self.assertEqual(owner.state, ConnectionState.OFFLINE)

    def test_stop_timeout_is_not_retried_and_ble_always_disconnects(self) -> None:
        class StopTimeoutBackend(SimSpherov2Backend):
            def stop(self) -> None:
                self.calls.append("stop_timeout")
                raise TimeoutError("injected stop acknowledgement timeout")

        backend = StopTimeoutBackend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver)
        owner.connect_for_stationary_probe()
        with self.assertRaisesRegex(TimeoutError, "stop acknowledgement"):
            owner.disconnect("test_timeout")
        self.assertEqual(backend.calls, ["connect", "stop_timeout", "disconnect"])
        self.assertFalse(driver.connected)
        self.assertTrue(owner.stopped)
        self.assertEqual(owner.state, ConnectionState.OFFLINE)

    def test_nonblocking_emergency_stop_prevents_disconnect_stop_retry(self) -> None:
        backend, driver, owner, _ = self.make_probe()
        owner.connect_for_stationary_probe()
        driver.dispatch_emergency_stop()
        owner.disconnect("emergency_stop_complete")
        self.assertEqual(backend.calls.count("stop_no_wait"), 1)
        self.assertNotIn("stop", backend.calls)
        self.assertEqual(backend.calls[-1], "disconnect")

    def test_bounded_forward_requires_connected_safe_hold_and_keeps_speed_cap(self) -> None:
        backend, driver, owner, _ = self.make_probe()
        with self.assertRaisesRegex(RuntimeError, "connected R2"):
            driver.dispatch_bounded_forward(5)
        owner.connect_for_stationary_probe()
        driver.dispatch_bounded_forward(5)
        self.assertEqual(backend.calls[-1], "forward_no_wait:5")
        self.assertFalse(driver.stopped)
        with self.assertRaisesRegex(RuntimeError, "stopped state"):
            driver.dispatch_bounded_forward(5)
        driver.dispatch_emergency_stop()
        self.assertTrue(driver.stopped)
        with self.assertRaises(ValueError):
            driver.dispatch_bounded_forward(26)
        owner.disconnect("bounded_forward_test_complete")

    def test_probe_records_stop_timeout_and_returns_failure_evidence(self) -> None:
        class StopTimeoutBackend(SimSpherov2Backend):
            def stop(self) -> None:
                self.calls.append("stop_timeout")
                raise TimeoutError("injected stop acknowledgement timeout")

        backend = StopTimeoutBackend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver)
        report = StationaryCapabilityProbe(owner, driver).run(
            generated_at="2030-01-01T00:00:00Z", evidence_category="HIL-stationary"
        )
        self.assertEqual(report.capabilities["stop.latency"].status, "failed")
        self.assertEqual(report.final_state, "disconnected_stop_unconfirmed")
        self.assertEqual(backend.calls.count("stop_timeout"), 1)
        self.assertEqual(backend.calls[-1], "disconnect")
        self.assertEqual(owner.state, ConnectionState.OFFLINE)

    def test_unavailable_backend_has_no_implicit_hardware_fallback(self) -> None:
        driver = Spherov2R2Driver(
            backend=UnavailableSpherov2Backend(), configured_identity="configured-outside-source"
        )
        with self.assertRaisesRegex(HardwareUnavailableError, "simulation/replay is mandatory"):
            driver.connect()
        self.assertTrue(driver.stopped)

    def test_immutable_record_and_hash_verified_replay(self) -> None:
        _, _, _, probe = self.make_probe()
        report = probe.run(generated_at="2030-01-01T00:00:00Z")
        with tempfile.TemporaryDirectory() as raw_temp:
            path = Path(raw_temp) / "report.json"
            digest = write_immutable_json(path, report.to_dict())
            replay = read_verified_json(path, digest)
            self.assertEqual(replay["final_state"], "safe_hold")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                read_verified_json(path, "0" * 64)
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_verified_replay_rejects_non_object_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw_temp:
            path = Path(raw_temp) / "report.json"
            path.write_text("[]", encoding="utf-8")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "root must be an object"):
                read_verified_json(path, digest)

    def test_canonical_replay_fixture_is_stationary_and_safe(self) -> None:
        path = Path(__file__).parent / "fixtures" / "sim-stationary-session.json"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        replay = read_verified_json(path, digest)
        self.assertEqual(replay["seed"], 20260811)
        self.assertFalse(replay["movement_performed"])
        self.assertEqual(replay["events"][-2:], ["stop", "disconnect"])
        self.assertEqual(replay["final_state"], "safe_hold")

    def test_critical_hardware_battery_blocks_all_optional_actions(self) -> None:
        class CriticalBatteryBackend(SimSpherov2Backend):
            def battery(self) -> dict[str, object]:
                self.calls.append("battery")
                return {"state": "critical", "voltage_v": 3.1, "provenance": "test"}

            def exercise_stationary(self, capability: str) -> dict[str, object]:
                raise AssertionError(f"unsafe action attempted: {capability}")

        backend = CriticalBatteryBackend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        report = StationaryCapabilityProbe(BleOwner(driver), driver).run(
            generated_at="2030-01-01T00:00:00Z", evidence_category="HIL-stationary"
        )
        for capability, evidence in report.capabilities.items():
            if capability not in {"identity.system_info", "battery.state_voltage"}:
                self.assertEqual(evidence.status, "untested")
        self.assertEqual(report.final_state, "safe_hold")

    def test_hil_failure_evidence_excludes_identity_and_exception_text(self) -> None:
        payload = build_hil_failure_evidence(
            error_type="TimeoutError",
            owner_state="offline",
            driver_connected=False,
            driver_stopped=True,
        )
        self.assertEqual(payload["terminal"], "failed")
        self.assertFalse(payload["movement_performed"])
        self.assertNotIn("configured-name", str(payload))
        self.assertNotIn("private exception detail", str(payload))
        self.assertNotIn("address", str(payload))

    def test_hil_failure_evidence_accepts_stable_error_stage(self) -> None:
        payload = build_hil_failure_evidence(
            error_type="StationaryExpressionError",
            error_stage="audio_volume_read",
            owner_state="offline",
            driver_connected=False,
            driver_stopped=True,
        )
        self.assertEqual(payload["error_stage"], "audio_volume_read")

    def test_probe_preserves_capability_phase_when_disconnect_also_fails(self) -> None:
        class DoubleFailureBackend(SimSpherov2Backend):
            def exercise_stationary(self, capability: str) -> dict[str, object]:
                if capability == "head.safe_range":
                    raise TimeoutError("private primary detail")
                return dict(super().exercise_stationary(capability))

            def disconnect(self) -> None:
                self.calls.append("disconnect_failed")
                self.connected = False
                raise EOFError("private cleanup detail")

        backend = DoubleFailureBackend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver)
        with self.assertRaises(CapabilityProbeError) as caught:
            StationaryCapabilityProbe(owner, driver).run(evidence_category="HIL-stationary")
        self.assertEqual(caught.exception.phase, "head.safe_range")
        self.assertEqual(caught.exception.error_type, "TimeoutError")
        self.assertEqual(caught.exception.cleanup_error_type, "EOFError")
        self.assertEqual(owner.state, ConnectionState.OFFLINE)
        self.assertNotIn("private", str(caught.exception))

    def test_probe_includes_sanitized_nested_backend_phase(self) -> None:
        class AudioFailureBackend(SimSpherov2Backend):
            def exercise_stationary(self, capability: str) -> dict[str, object]:
                if capability == "audio.quiet_preview":
                    from r2_runtime.spherov2_backend import StationaryExpressionError

                    raise StationaryExpressionError("audio_volume_read", "IndexError")
                return dict(super().exercise_stationary(capability))

        backend = AudioFailureBackend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        with self.assertRaises(CapabilityProbeError) as caught:
            StationaryCapabilityProbe(BleOwner(driver), driver).run(
                evidence_category="HIL-stationary"
            )
        self.assertEqual(caught.exception.phase, "audio.quiet_preview.audio_volume_read")
        self.assertEqual(caught.exception.error_type, "IndexError")


if __name__ == "__main__":
    unittest.main()
