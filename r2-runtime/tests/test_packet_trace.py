from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from r2_runtime.packet_trace import (
    StopResponseTraceRecorder,
    classify_stop_response_trace,
    physical_state_for_trace,
)
from r2_runtime.session_recording import SessionClock


class _UtcTicks:
    def __init__(self) -> None:
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        result = self.now
        self.now += timedelta(milliseconds=5)
        return result


class PacketTraceTest(unittest.TestCase):
    def make_recorder(self) -> StopResponseTraceRecorder:
        monotonic = iter((1000, 2000, 3000))
        return StopResponseTraceRecorder(
            session_ref="session-abcdef0123456789",
            clock=SessionClock("sim-clock-abcdef01", "deterministic", 0.0),
            utc_now=_UtcTicks(),
            monotonic_ns=lambda: next(monotonic),
        )

    def test_matching_success_is_sanitized_and_classified(self) -> None:
        recorder = self.make_recorder()
        recorder.record(
            direction="tx",
            did=22,
            cid=1,
            protocol_sequence=7,
            flags=10,
            encoded_packet=b"private outgoing bytes",
        )
        recorder.record(
            direction="rx",
            did=22,
            cid=1,
            protocol_sequence=7,
            flags=1,
            encoded_packet=b"private response bytes",
            error="success",
        )
        payload = recorder.finalize(
            owner_state="offline", ble_connections=0, physical_state="normal"
        )
        self.assertEqual(classify_stop_response_trace(payload), "acknowledged_success")
        serialized = str(payload)
        self.assertNotIn("private outgoing bytes", serialized)
        self.assertNotIn("private response bytes", serialized)
        self.assertNotIn("address", serialized.lower())

    def test_timeout_remains_unconfirmed_and_retry_is_rejected(self) -> None:
        recorder = self.make_recorder()
        arguments = dict(
            direction="tx",
            did=22,
            cid=1,
            protocol_sequence=9,
            flags=10,
            encoded_packet=b"one stop command",
        )
        recorder.record(**arguments)
        with self.assertRaisesRegex(ValueError, "retry is prohibited"):
            recorder.record(**arguments)
        payload = recorder.finalize(
            owner_state="offline", ble_connections=0, physical_state="normal"
        )
        self.assertEqual(classify_stop_response_trace(payload), "stop_unconfirmed")

    def test_error_cleanup_and_tampering_classification(self) -> None:
        recorder = self.make_recorder()
        recorder.record(
            direction="tx",
            did=22,
            cid=1,
            protocol_sequence=2,
            flags=10,
            encoded_packet=b"command",
        )
        recorder.record(
            direction="rx",
            did=22,
            cid=1,
            protocol_sequence=2,
            flags=1,
            encoded_packet=b"error",
            error="command_failed",
        )
        payload = recorder.finalize(
            owner_state="offline", ble_connections=0, physical_state="normal"
        )
        self.assertEqual(classify_stop_response_trace(payload), "acknowledged_error")
        bad_cleanup = deepcopy(payload)
        bad_cleanup["cleanup"]["ble_connections"] = 1
        self.assertEqual(classify_stop_response_trace(bad_cleanup), "invalid_test")
        injected = deepcopy(payload)
        injected["observations"][0]["payload"] = "not allowed"
        with self.assertRaisesRegex(ValueError, "unapproved fields"):
            classify_stop_response_trace(injected)
        uncorrelated = deepcopy(payload)
        uncorrelated["observations"][1]["protocol_sequence"] = 3
        with self.assertRaisesRegex(ValueError, "does not correlate"):
            classify_stop_response_trace(uncorrelated)

    def test_non_stop_command_is_rejected_before_recording(self) -> None:
        with self.assertRaisesRegex(ValueError, "only raw-motor"):
            self.make_recorder().record(
                direction="tx",
                did=22,
                cid=7,
                protocol_sequence=1,
                flags=10,
                encoded_packet=b"heading-bearing command",
            )

    def test_hil_evidence_category_uses_sanitized_lowercase_vocabulary(self) -> None:
        recorder = StopResponseTraceRecorder(
            session_ref="session-abcdef0123456789",
            clock=SessionClock("sim-clock-abcdef01", "deterministic", 0.0),
            evidence_category="hil-stationary",
        )
        self.assertEqual(recorder.evidence_category, "hil-stationary")
        with self.assertRaisesRegex(ValueError, "invalid evidence category"):
            StopResponseTraceRecorder(
                session_ref="session-abcdef0123456789",
                clock=SessionClock("sim-clock-abcdef01", "deterministic", 0.0),
                evidence_category="HIL-stationary",
            )

    def test_physical_confirmation_preserves_expected_timeout_classification(self) -> None:
        self.assertEqual(
            physical_state_for_trace(operator_confirmed=True, error_type="TimeoutError"),
            "normal",
        )
        self.assertEqual(
            physical_state_for_trace(operator_confirmed=True, error_type="UnsafeBatteryState"),
            "unconfirmed",
        )
        self.assertEqual(
            physical_state_for_trace(operator_confirmed=False, error_type=None),
            "unconfirmed",
        )


if __name__ == "__main__":
    unittest.main()
