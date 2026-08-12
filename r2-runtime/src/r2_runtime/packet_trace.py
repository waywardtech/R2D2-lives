"""Sanitized one-command metadata trace for the R201 stop-response bench."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import re
import time
from typing import Callable, Mapping, Sequence

from .session_recording import SessionClock
from .ble_owner import ConnectionState

_OPAQUE_SESSION_REF = re.compile(r"^session-[0-9a-f]{16,64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_CLOCK_ID = re.compile(r"^(?:sim-)?clock-[0-9a-f]{8,64}$")
_SYNC_SOURCES = {"deterministic", "ntp", "chrony", "unsynchronized"}
_RESPONSE_ERRORS = {
    "success", "bad_device_id", "bad_command_id", "not_yet_implemented",
    "command_is_restricted", "bad_data_length", "command_failed",
    "bad_parameter_value", "busy", "bad_target_id", "target_unavailable",
}
_TRACE_KEYS = {
    "schema_version", "evidence_category", "session_ref", "trace_kind",
    "movement_performed", "observations", "cleanup",
}
_OBSERVATION_KEYS = {
    "sequence", "occurred_at", "monotonic_ns", "clock", "direction", "did",
    "cid", "protocol_sequence", "flags", "byte_count", "packet_sha256", "error",
}
_CLOCK_KEYS = {"clock_id", "sync_source", "uncertainty_ms"}
_CLEANUP_KEYS = {"owner_state", "ble_connections", "physical_state"}


@dataclass(frozen=True)
class PacketMetadata:
    sequence: int
    occurred_at: str
    monotonic_ns: int
    clock: SessionClock
    direction: str
    did: int
    cid: int
    protocol_sequence: int
    flags: int
    byte_count: int
    packet_sha256: str
    error: str | None


class StopResponseTraceRecorder:
    """Retains hashes and decoded headers only; encoded packet bytes are discarded."""

    def __init__(
        self,
        *,
        session_ref: str,
        clock: SessionClock,
        evidence_category: str = "simulation",
        utc_now: Callable[[], datetime] | None = None,
        monotonic_ns: Callable[[], int] = time.monotonic_ns,
    ) -> None:
        if not _OPAQUE_SESSION_REF.fullmatch(session_ref):
            raise ValueError("session_ref must be opaque")
        if not re.fullmatch(r"[a-z0-9_.:-]+", evidence_category):
            raise ValueError("invalid evidence category")
        if clock.uncertainty_ms < 0:
            raise ValueError("clock uncertainty must be non-negative")
        if not _OPAQUE_CLOCK_ID.fullmatch(clock.clock_id):
            raise ValueError("clock_id must be opaque")
        if clock.sync_source not in _SYNC_SOURCES:
            raise ValueError("unsupported clock synchronization source")
        self.session_ref = session_ref
        self.clock = clock
        self.evidence_category = evidence_category
        self._utc_now = utc_now or (lambda: datetime.now(timezone.utc))
        self._monotonic_ns = monotonic_ns
        self._observations: list[PacketMetadata] = []

    def record(
        self,
        *,
        direction: str,
        did: int,
        cid: int,
        protocol_sequence: int,
        flags: int,
        encoded_packet: bytes,
        error: str | None = None,
    ) -> None:
        if (did, cid) != (22, 1):
            raise ValueError("trace accepts only raw-motor DID 22 CID 1")
        if direction not in {"tx", "rx"}:
            raise ValueError("packet direction must be tx or rx")
        if any(not 0 <= value <= 255 for value in (did, cid, protocol_sequence, flags)):
            raise ValueError("packet header byte is out of range")
        tx = [item for item in self._observations if item.direction == "tx"]
        rx = [item for item in self._observations if item.direction == "rx"]
        if direction == "tx" and tx:
            raise ValueError("stop command retry is prohibited")
        if direction == "rx" and (not tx or rx):
            raise ValueError("response must follow exactly one stop command")
        if direction == "tx" and error is not None:
            raise ValueError("transmitted command cannot contain a response error")
        if direction == "rx" and error not in _RESPONSE_ERRORS:
            raise ValueError("response requires a decoded error status")
        now = self._utc_now()
        if now.tzinfo is None or now.utcoffset() != timezone.utc.utcoffset(now):
            raise ValueError("trace clock must return UTC")
        self._observations.append(
            PacketMetadata(
                sequence=len(self._observations) + 1,
                occurred_at=now.isoformat().replace("+00:00", "Z"),
                monotonic_ns=self._monotonic_ns(),
                clock=self.clock,
                direction=direction,
                did=did,
                cid=cid,
                protocol_sequence=protocol_sequence,
                flags=flags,
                byte_count=len(encoded_packet),
                packet_sha256=hashlib.sha256(encoded_packet).hexdigest(),
                error=error,
            )
        )

    def finalize(
        self, *, owner_state: str, ble_connections: int, physical_state: str
    ) -> dict[str, object]:
        if owner_state not in {state.value for state in ConnectionState}:
            raise ValueError("invalid cleanup owner state")
        if isinstance(ble_connections, bool) or not isinstance(ble_connections, int) or ble_connections < 0:
            raise ValueError("invalid cleanup BLE connection count")
        if physical_state not in {"normal", "unconfirmed"}:
            raise ValueError("invalid cleanup physical state")
        return {
            "schema_version": "1.0",
            "evidence_category": self.evidence_category,
            "session_ref": self.session_ref,
            "trace_kind": "r201.raw_motor_off_response",
            "movement_performed": False,
            "observations": [asdict(item) for item in self._observations],
            "cleanup": {
                "owner_state": owner_state,
                "ble_connections": ble_connections,
                "physical_state": physical_state,
            },
        }


def classify_stop_response_trace(payload: Mapping[str, object]) -> str:
    """Strictly validate sanitized evidence and classify the response outcome."""

    if set(payload) != _TRACE_KEYS or payload.get("schema_version") != "1.0":
        raise ValueError("invalid stop trace envelope")
    if payload.get("trace_kind") != "r201.raw_motor_off_response":
        raise ValueError("invalid stop trace kind")
    if payload.get("movement_performed") is not False:
        raise ValueError("stop-response trace cannot claim movement")
    session_ref = payload.get("session_ref")
    if not isinstance(session_ref, str) or not _OPAQUE_SESSION_REF.fullmatch(session_ref):
        raise ValueError("invalid opaque session reference")
    observations = payload.get("observations")
    if not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)):
        raise ValueError("trace observations must be a sequence")
    if len(observations) not in {1, 2}:
        raise ValueError("trace must contain one command and at most one response")

    previous_monotonic = -1
    protocol_sequence: int | None = None
    response_error: str | None = None
    for index, item in enumerate(observations, 1):
        if not isinstance(item, Mapping) or set(item) != _OBSERVATION_KEYS:
            raise ValueError("trace observation contains unapproved fields")
        expected_direction = "tx" if index == 1 else "rx"
        if item.get("sequence") != index or item.get("direction") != expected_direction:
            raise ValueError("trace ordering is invalid")
        if (item.get("did"), item.get("cid")) != (22, 1):
            raise ValueError("trace contains a non-stop command")
        current_protocol_sequence = item.get("protocol_sequence")
        if isinstance(current_protocol_sequence, bool) or not isinstance(current_protocol_sequence, int):
            raise ValueError("invalid protocol sequence")
        if protocol_sequence is None:
            protocol_sequence = current_protocol_sequence
        elif current_protocol_sequence != protocol_sequence:
            raise ValueError("response does not correlate to command")
        for byte_key in ("protocol_sequence", "flags"):
            value = item.get(byte_key)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
                raise ValueError("invalid packet header byte")
        byte_count = item.get("byte_count")
        if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count <= 0:
            raise ValueError("invalid packet byte count")
        packet_sha256 = item.get("packet_sha256")
        if not isinstance(packet_sha256, str) or not _SHA256.fullmatch(packet_sha256):
            raise ValueError("invalid packet hash")
        occurred_at = item.get("occurred_at")
        if not isinstance(occurred_at, str) or not occurred_at.endswith("Z"):
            raise ValueError("trace time must be RFC 3339 UTC")
        datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        monotonic_ns = item.get("monotonic_ns")
        if isinstance(monotonic_ns, bool) or not isinstance(monotonic_ns, int) or monotonic_ns < previous_monotonic:
            raise ValueError("trace monotonic time regressed")
        previous_monotonic = monotonic_ns
        raw_clock = item.get("clock")
        if not isinstance(raw_clock, Mapping) or set(raw_clock) != _CLOCK_KEYS:
            raise ValueError("invalid trace clock")
        uncertainty = raw_clock.get("uncertainty_ms")
        if not isinstance(raw_clock.get("clock_id"), str) or not _OPAQUE_CLOCK_ID.fullmatch(raw_clock["clock_id"]):
            raise ValueError("invalid trace clock identity")
        if raw_clock.get("sync_source") not in _SYNC_SOURCES:
            raise ValueError("invalid trace clock sync source")
        if isinstance(uncertainty, bool) or not isinstance(uncertainty, (int, float)) or uncertainty < 0:
            raise ValueError("invalid trace clock uncertainty")
        error = item.get("error")
        if index == 1 and error is not None:
            raise ValueError("command observation cannot contain response error")
        if index == 2:
            if error not in _RESPONSE_ERRORS:
                raise ValueError("invalid decoded response error")
            response_error = error

    cleanup = payload.get("cleanup")
    if not isinstance(cleanup, Mapping) or set(cleanup) != _CLEANUP_KEYS:
        raise ValueError("invalid cleanup evidence")
    if cleanup.get("owner_state") != "offline" or cleanup.get("ble_connections") != 0:
        return "invalid_test"
    if cleanup.get("physical_state") != "normal":
        return "invalid_test"
    if response_error is None:
        return "stop_unconfirmed"
    return "acknowledged_success" if response_error == "success" else "acknowledged_error"
