from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
from uuid import UUID

from sap_protocol.generated import (
    ClockQuality,
    CommandRequest,
    CommandStatus,
    EventEnvelope,
    SAP_VERSION,
    SessionRequest,
    SessionResponse,
)

from .drivers import SimDroidDriver


def _uuid(counter: int) -> str:
    return str(UUID(int=counter))


class SimAgentServer:
    """Deterministic in-process SAP Agent; commands always end stopped."""

    capabilities = {"command.stop", "command.safe_hold", "command.hold_pose"}

    def __init__(self, *, seed: int = 20260811) -> None:
        self.seed = seed
        self.driver = SimDroidDriver()
        self._sessions: set[str] = set()
        self._events: list[EventEnvelope] = []
        self._statuses: dict[str, CommandStatus] = {}
        self._idempotency: dict[str, CommandStatus] = {}
        self._counter = seed

    def _next_uuid(self) -> str:
        self._counter += 1
        return _uuid(self._counter)

    def create_session(self, request: SessionRequest) -> SessionResponse:
        common = tuple(sorted(set(request.protocol_versions) & {SAP_VERSION}))
        rejected = tuple(cap for cap in request.required_capabilities if cap not in self.capabilities)
        if not common or rejected:
            raise ValueError(f"sap.capability_missing:{','.join(rejected)}")
        session_id = self._next_uuid()
        self._sessions.add(session_id)
        expires = datetime(2030, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=request.requested_duration_s)
        return SessionResponse(
            session_id=session_id,
            selected_protocol_version=common[-1],
            accepted_capabilities=tuple(sorted(self.capabilities)),
            expires_at=expires.isoformat().replace("+00:00", "Z"),
            event_cursor="0",
        )

    def submit_command(self, request: CommandRequest) -> CommandStatus:
        previous = self._idempotency.get(request.idempotency_key)
        if previous is not None:
            return previous
        if request.session_id not in self._sessions:
            return self._terminal(request, "rejected", "sap.session_expired")
        deadline = datetime.fromisoformat(request.deadline.replace("Z", "+00:00"))
        if deadline <= datetime.now(timezone.utc):
            return self._terminal(request, "rejected", "sap.command_stale")
        if request.type not in self.capabilities_as_commands():
            return self._terminal(request, "rejected", "sap.capability_missing")
        self.driver.safe_hold()
        status = self._terminal(request, "succeeded", None)
        self._idempotency[request.idempotency_key] = status
        return status

    def capabilities_as_commands(self) -> set[str]:
        return {item.removeprefix("command.") for item in self.capabilities}

    def _terminal(self, request: CommandRequest, state: str, reason: str | None) -> CommandStatus:
        updated_at = "2030-01-01T00:00:00Z"
        status = CommandStatus(request.command_id, state, updated_at, reason, {"safe_state": "safe_hold"})
        self._statuses[request.command_id] = status
        pose = {
            "frame_id": "urn:sap:frame:agent:simulation:r2:odom",
            "child_frame_id": "urn:sap:frame:agent:simulation:r2:base_link",
            "position_m": {"x": 0.0, "y": 0.0, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
            "covariance_6x6": tuple(0.0 for _ in range(36)),
            "status": "valid",
            "confidence": 1.0,
            "source": "deterministic_simulator_truth",
            "valid_until": updated_at,
            "map_revision": None,
        }
        event = EventEnvelope(
            schema_version=SAP_VERSION,
            event_id=self._next_uuid(),
            event_type=f"agent.command.{state}",
            producer_id="urn:sap:agent:simulation:r2",
            session_id=request.session_id,
            correlation_id=request.correlation_id,
            causation_id=request.command_id,
            sequence=len(self._events) + 1,
            occurred_at=updated_at,
            monotonic_ns=time.monotonic_ns(),
            clock=ClockQuality("sim-clock", "simulation", 0.0, synchronized=True),
            payload={
                "command_id": request.command_id,
                "state": state,
                "safe_state": "safe_hold",
                "pose": pose,
            },
        )
        self._events.append(event)
        return status

    def events_after(self, cursor: str) -> tuple[EventEnvelope, ...]:
        sequence = int(cursor)
        return tuple(event for event in self._events if event.sequence > sequence)
