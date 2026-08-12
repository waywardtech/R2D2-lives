from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from r2_runtime.ble_owner import BleOwner, ConnectionState
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.session_recording import (
    SessionClock,
    StationarySessionRecorder,
    replay_stationary_session,
)
from r2_runtime.sim_hardware import SimSpherov2Backend


class _TickingUtc:
    def __init__(self) -> None:
        self.value = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        result = self.value
        self.value += timedelta(milliseconds=10)
        return result


class SessionRecordingTest(unittest.TestCase):
    def make_session(self) -> tuple[StationarySessionRecorder, BleOwner]:
        ticks = iter(range(1_000, 20_000, 1_000))
        recorder = StationarySessionRecorder(
            session_ref="session-2026081100000000",
            clock=SessionClock("sim-clock-20260811", "deterministic", 0.0),
            utc_now=_TickingUtc(),
            monotonic_ns=lambda: next(ticks),
        )
        backend = SimSpherov2Backend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver, event_sink=recorder.record_owner_event)
        owner.connect_for_stationary_probe()
        driver.safe_hold()
        owner.mark_ready()
        owner.disconnect("stationary_probe_complete")
        return recorder, owner

    def test_owner_lifecycle_round_trips_without_identity_or_ble_payload(self) -> None:
        recorder, owner = self.make_session()
        payload = recorder.to_dict()
        replay = replay_stationary_session(payload)
        self.assertFalse(owner.event_sink_failed)
        self.assertEqual([event.sequence for event in replay], list(range(1, 7)))
        self.assertEqual(replay[0].state, ConnectionState.OFFLINE.value)
        self.assertEqual(replay[-1].state, ConnectionState.OFFLINE.value)
        serialized = str(payload)
        self.assertNotIn("D2-SIMULATED", serialized)
        self.assertNotIn("address", serialized.lower())
        self.assertNotIn("packet", serialized.lower())

    def test_canonical_lifecycle_fixture_replays_to_offline(self) -> None:
        path = Path(__file__).parent / "fixtures" / "sim-owner-lifecycle-session.json"
        replay = replay_stationary_session(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(len(replay), 6)
        self.assertEqual(replay[-1].state, ConnectionState.OFFLINE.value)
        self.assertEqual(replay[-1].reason, "disconnected_safe_hold")

    def test_external_disconnect_reason_is_redacted(self) -> None:
        ticks = iter(range(1_000, 20_000, 1_000))
        recorder = StationarySessionRecorder(
            session_ref="session-0123456789abcdef",
            clock=SessionClock("sim-clock-20260811", "deterministic", 0.0),
            utc_now=_TickingUtc(),
            monotonic_ns=lambda: next(ticks),
        )
        backend = SimSpherov2Backend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver, event_sink=recorder.record_owner_event)
        owner.connect_for_stationary_probe()
        owner.disconnect("D2-PRIVATE-NAME")
        payload = recorder.to_dict()
        self.assertNotIn("D2-PRIVATE-NAME", str(payload))
        self.assertEqual(payload["events"][-2]["reason"], "external_reason_redacted")
        replay_stationary_session(payload)

    def test_replay_rejects_movement_sequence_and_time_tampering(self) -> None:
        recorder, _ = self.make_session()
        baseline = recorder.to_dict()
        moved = deepcopy(baseline)
        moved["movement_performed"] = True
        with self.assertRaisesRegex(ValueError, "cannot contain movement"):
            replay_stationary_session(moved)
        skipped = deepcopy(baseline)
        skipped["events"][2]["sequence"] = 9
        with self.assertRaisesRegex(ValueError, "not contiguous"):
            replay_stationary_session(skipped)
        regressed = deepcopy(baseline)
        regressed["events"][3]["monotonic_ns"] = 1
        with self.assertRaisesRegex(ValueError, "regressed"):
            replay_stationary_session(regressed)
        injected = deepcopy(baseline)
        injected["events"][1]["device_address"] = "private"
        with self.assertRaisesRegex(ValueError, "unapproved fields"):
            replay_stationary_session(injected)
        invalid_transition = deepcopy(baseline)
        invalid_transition["events"][2]["state"] = "ready"
        with self.assertRaisesRegex(ValueError, "invalid owner state transition"):
            replay_stationary_session(invalid_transition)

    def test_recorder_failure_cannot_interrupt_disconnect(self) -> None:
        backend = SimSpherov2Backend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")

        def broken_sink(_: object) -> None:
            raise RuntimeError("injected recorder failure")

        owner = BleOwner(driver, event_sink=broken_sink)
        owner.connect_for_stationary_probe()
        owner.disconnect("test_complete")
        self.assertTrue(owner.event_sink_failed)
        self.assertTrue(owner.stopped)
        self.assertEqual(owner.state, ConnectionState.OFFLINE)
        self.assertEqual(backend.calls[-2:], ["stop", "disconnect"])


if __name__ == "__main__":
    unittest.main()
