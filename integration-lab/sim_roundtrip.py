"""P0 deterministic SAP round-trip; no network, BLE, audio, or motors."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from r2_runtime.sim_agent import SimAgentServer
from sap_protocol.generated import CommandRequest, Pose, SessionRequest

SEED = 20260811


def run_roundtrip() -> dict[str, object]:
    server = SimAgentServer(seed=SEED)
    session = server.create_session(
        SessionRequest(
            peer_id="urn:sap:provider:simulation:bsm",
            protocol_versions=("0.1.0",),
            required_capabilities=("command.safe_hold",),
            requested_duration_s=60,
        )
    )
    command_id = str(UUID(int=SEED + 100))
    correlation_id = str(UUID(int=SEED + 101))
    deadline = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    command = CommandRequest(
        command_id=command_id,
        idempotency_key="p0-safe-hold-1",
        session_id=session.session_id,
        type="safe_hold",
        parameters={"reason": "phase-0 simulation smoke"},
        deadline=deadline,
        correlation_id=correlation_id,
        preconditions={"driver": "simulation"},
    )
    first = server.submit_command(command)
    duplicate = server.submit_command(command)
    events = server.events_after(session.event_cursor)
    assert first is duplicate
    assert first.state == "succeeded"
    assert server.driver.stopped
    assert len(events) == 1
    event = events[0]
    pose = Pose.from_dict(event.payload["pose"])
    assert event.session_id == session.session_id
    assert event.correlation_id == correlation_id
    assert event.causation_id == command_id
    assert event.clock.sync_source == "simulation"
    assert event.clock.uncertainty_ms == 0.0
    assert event.monotonic_ns >= 0
    assert event.payload["safe_state"] == "safe_hold"
    assert pose.frame_id == "urn:sap:frame:agent:simulation:r2:odom"
    assert pose.position_m == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert pose.covariance_6x6 == tuple(0.0 for _ in range(36))
    assert pose.source == "deterministic_simulator_truth"
    return {
        "seed": SEED,
        "session_id": session.session_id,
        "command_id": command_id,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "frame_id": pose.frame_id,
        "position_m": pose.position_m,
        "pose_confidence": pose.confidence,
        "pose_covariance_values": len(pose.covariance_6x6 or ()),
        "pose_provenance": pose.source,
        "clock": event.clock.to_dict(),
        "safe_state": event.payload["safe_state"],
        "duplicate_suppressed": True,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_roundtrip(), indent=2, sort_keys=True))
