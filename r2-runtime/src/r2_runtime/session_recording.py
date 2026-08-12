"""Privacy-safe BLE-owner lifecycle recording and deterministic replay."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
import time
from typing import Callable, Mapping, Sequence

from .ble_owner import ConnectionState, OwnerEvent

_SAFE_TOKEN = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_OPAQUE_SESSION_REF = re.compile(r"^session-[0-9a-f]{16,64}$")
_RECORDED_REASONS = {
    "startup_safe_hold",
    "stationary_probe",
    "connect_failed_safe",
    "connected_stopped",
    "stationary_probe_complete",
    "disconnected_safe_hold",
    "link_lost_no_resume",
    "requested",
    "external_reason_redacted",
}
_TOP_LEVEL_KEYS = {
    "schema_version",
    "evidence_category",
    "session_ref",
    "movement_performed",
    "events",
}
_EVENT_KEYS = {
    "schema_version",
    "sequence",
    "event_type",
    "occurred_at",
    "monotonic_ns",
    "clock",
    "state",
    "reason",
}
_CLOCK_KEYS = {"clock_id", "sync_source", "uncertainty_ms"}


@dataclass(frozen=True)
class SessionClock:
    clock_id: str
    sync_source: str
    uncertainty_ms: float


@dataclass(frozen=True)
class RecordedOwnerEvent:
    schema_version: str
    sequence: int
    event_type: str
    occurred_at: str
    monotonic_ns: int
    clock: SessionClock
    state: str
    reason: str


class StationarySessionRecorder:
    """Records only allowlisted owner state and reason tokens, never BLE data."""

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
            raise ValueError("session_ref must be an opaque session token")
        for label, value in (
            ("clock_id", clock.clock_id),
            ("sync_source", clock.sync_source),
            ("evidence_category", evidence_category),
        ):
            if not _SAFE_TOKEN.fullmatch(value):
                raise ValueError(f"{label} must be a privacy-safe token")
        if clock.uncertainty_ms < 0:
            raise ValueError("clock uncertainty must be non-negative")
        self.session_ref = session_ref
        self.clock = clock
        self.evidence_category = evidence_category
        self._utc_now = utc_now or (lambda: datetime.now(timezone.utc))
        self._monotonic_ns = monotonic_ns
        self._events: list[RecordedOwnerEvent] = []

    def record_owner_event(self, event: OwnerEvent) -> None:
        state = event.state.value
        reason = (
            event.reason
            if event.reason in _RECORDED_REASONS
            else "external_reason_redacted"
        )
        now = self._utc_now()
        if now.tzinfo is None or now.utcoffset() != timezone.utc.utcoffset(now):
            raise ValueError("session UTC clock must return a UTC-aware datetime")
        self._events.append(
            RecordedOwnerEvent(
                schema_version="1.0",
                sequence=event.sequence,
                event_type="owner.state.transition",
                occurred_at=now.isoformat().replace("+00:00", "Z"),
                monotonic_ns=self._monotonic_ns(),
                clock=self.clock,
                state=state,
                reason=reason,
            )
        )

    @property
    def events(self) -> tuple[RecordedOwnerEvent, ...]:
        return tuple(self._events)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "evidence_category": self.evidence_category,
            "session_ref": self.session_ref,
            "movement_performed": False,
            "events": [asdict(event) for event in self._events],
        }


def replay_stationary_session(payload: Mapping[str, object]) -> tuple[RecordedOwnerEvent, ...]:
    """Validate sequence/time/state invariants and return immutable replay events."""

    if payload.get("schema_version") != "1.0":
        raise ValueError("unsupported session recording schema")
    if set(payload) != _TOP_LEVEL_KEYS:
        raise ValueError("session recording contains unapproved fields")
    if payload.get("movement_performed") is not False:
        raise ValueError("stationary session cannot contain movement")
    session_ref = payload.get("session_ref")
    if not isinstance(session_ref, str) or not _OPAQUE_SESSION_REF.fullmatch(session_ref):
        raise ValueError("invalid opaque session_ref")
    evidence_category = payload.get("evidence_category")
    if not isinstance(evidence_category, str) or not _SAFE_TOKEN.fullmatch(evidence_category):
        raise ValueError("invalid privacy-safe evidence_category")
    raw_events = payload.get("events")
    if not isinstance(raw_events, Sequence) or isinstance(raw_events, (str, bytes)):
        raise ValueError("session events must be a sequence")

    replayed: list[RecordedOwnerEvent] = []
    previous_monotonic = -1
    for expected_sequence, raw in enumerate(raw_events, 1):
        if not isinstance(raw, Mapping):
            raise ValueError("session event must be an object")
        if set(raw) != _EVENT_KEYS:
            raise ValueError("session event contains unapproved fields")
        if raw.get("schema_version") != "1.0" or raw.get("event_type") != "owner.state.transition":
            raise ValueError("unsupported session event")
        if raw.get("sequence") != expected_sequence:
            raise ValueError("session event sequence is not contiguous")
        state = raw.get("state")
        reason = raw.get("reason")
        if state not in {member.value for member in ConnectionState}:
            raise ValueError("unknown owner state")
        if reason not in _RECORDED_REASONS:
            raise ValueError("unsafe owner reason")
        occurred_at = raw.get("occurred_at")
        if not isinstance(occurred_at, str) or not occurred_at.endswith("Z"):
            raise ValueError("event time must be RFC 3339 UTC")
        datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        monotonic_ns = raw.get("monotonic_ns")
        if isinstance(monotonic_ns, bool) or not isinstance(monotonic_ns, int) or monotonic_ns < previous_monotonic:
            raise ValueError("event monotonic time regressed")
        previous_monotonic = monotonic_ns
        raw_clock = raw.get("clock")
        if not isinstance(raw_clock, Mapping):
            raise ValueError("event clock is required")
        if set(raw_clock) != _CLOCK_KEYS:
            raise ValueError("event clock contains unapproved fields")
        clock_id = raw_clock.get("clock_id")
        sync_source = raw_clock.get("sync_source")
        uncertainty_ms = raw_clock.get("uncertainty_ms")
        if not isinstance(clock_id, str) or not _SAFE_TOKEN.fullmatch(clock_id):
            raise ValueError("invalid clock identity")
        if not isinstance(sync_source, str) or not _SAFE_TOKEN.fullmatch(sync_source):
            raise ValueError("invalid clock sync source")
        if not isinstance(uncertainty_ms, (int, float)) or uncertainty_ms < 0:
            raise ValueError("invalid clock uncertainty")
        replayed.append(
            RecordedOwnerEvent(
                schema_version="1.0",
                sequence=expected_sequence,
                event_type="owner.state.transition",
                occurred_at=occurred_at,
                monotonic_ns=monotonic_ns,
                clock=SessionClock(clock_id, sync_source, float(uncertainty_ms)),
                state=state,
                reason=reason,
            )
        )
    if not replayed or replayed[0].state != ConnectionState.OFFLINE.value:
        raise ValueError("session must begin offline")
    allowed_transitions = {
        ConnectionState.OFFLINE.value: {ConnectionState.CONNECTING.value},
        ConnectionState.CONNECTING.value: {
            ConnectionState.PROBING.value,
            ConnectionState.OFFLINE.value,
        },
        ConnectionState.PROBING.value: {
            ConnectionState.READY.value,
            ConnectionState.DISCONNECTING.value,
            ConnectionState.OFFLINE.value,
        },
        ConnectionState.READY.value: {
            ConnectionState.DISCONNECTING.value,
            ConnectionState.OFFLINE.value,
        },
        ConnectionState.DEGRADED.value: {
            ConnectionState.DISCONNECTING.value,
            ConnectionState.OFFLINE.value,
        },
        ConnectionState.DISCONNECTING.value: {ConnectionState.OFFLINE.value},
    }
    for previous, current in zip(replayed, replayed[1:]):
        if current.state not in allowed_transitions.get(previous.state, set()):
            raise ValueError("invalid owner state transition")
    if replayed[-1].state != ConnectionState.OFFLINE.value:
        raise ValueError("session must end offline")
    return tuple(replayed)
