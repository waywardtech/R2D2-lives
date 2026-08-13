"""Deterministic, hardware-free stop-response trace scenario matrix."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from .packet_trace import StopResponseTraceRecorder, classify_stop_response_trace
from .session_recording import SessionClock


class _Ticks:
    def __init__(self) -> None:
        self.utc = datetime(2030, 1, 1, tzinfo=timezone.utc)
        self.monotonic = 1_000

    def utc_now(self) -> datetime:
        value = self.utc
        self.utc += timedelta(milliseconds=5)
        return value

    def monotonic_ns(self) -> int:
        value = self.monotonic
        self.monotonic += 1_000
        return value


def _trace(*, response: str | None = None) -> dict[str, object]:
    ticks = _Ticks()
    recorder = StopResponseTraceRecorder(
        session_ref="session-0123456789abcdef",
        clock=SessionClock("sim-clock-abcdef01", "deterministic", 0.0),
        utc_now=ticks.utc_now,
        monotonic_ns=ticks.monotonic_ns,
    )
    recorder.record(
        direction="tx",
        did=22,
        cid=1,
        protocol_sequence=7,
        flags=10,
        encoded_packet=b"simulated-stop-command",
    )
    if response is not None:
        recorder.record(
            direction="rx",
            did=22,
            cid=1,
            protocol_sequence=7,
            flags=1,
            encoded_packet=b"simulated-stop-response",
            error=response,
        )
    return recorder.finalize(owner_state="offline", ble_connections=0, physical_state="normal")


def stop_response_matrix() -> dict[str, object]:
    """Return stable outcome evidence without importing BLE or sending packets."""

    success = _trace(response="success")
    firmware_error = _trace(response="command_failed")
    timeout = _trace()
    cleanup_failure = deepcopy(success)
    cleanup_failure["cleanup"]["ble_connections"] = 1  # type: ignore[index]
    sequence_mismatch = deepcopy(success)
    sequence_mismatch["observations"][1]["protocol_sequence"] = 8  # type: ignore[index]

    scenarios: list[tuple[str, dict[str, object]]] = [
        ("acknowledged_success", success),
        ("acknowledged_firmware_error", firmware_error),
        ("response_timeout", timeout),
        ("cleanup_failure", cleanup_failure),
        ("sequence_mismatch", sequence_mismatch),
    ]
    results: list[dict[str, str]] = []
    for name, evidence in scenarios:
        try:
            outcome = classify_stop_response_trace(evidence)
        except ValueError as error:
            outcome = f"rejected:{error}"
        results.append({"scenario": name, "outcome": outcome})
    return {
        "schema_version": "1.0",
        "simulation_seed": 20260811,
        "hardware_accessed": False,
        "movement_performed": False,
        "results": results,
    }
