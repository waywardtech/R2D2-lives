from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID
import unittest

from r2_runtime.sim_agent import SimAgentServer
from sap_protocol.generated import CommandRequest, Pose, SessionRequest


class SimulationRoundTripTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = SimAgentServer(seed=7)
        self.session = self.server.create_session(
            SessionRequest(
                peer_id="urn:sap:provider:test",
                protocol_versions=("0.1.0",),
                required_capabilities=("command.safe_hold",),
                requested_duration_s=30,
            )
        )

    def command(self, *, command_id: int = 100, key: str = "key", stale: bool = False) -> CommandRequest:
        delta = timedelta(seconds=-1 if stale else 30)
        return CommandRequest(
            command_id=str(UUID(int=command_id)),
            idempotency_key=key,
            session_id=self.session.session_id,
            type="safe_hold",
            parameters={},
            deadline=(datetime.now(timezone.utc) + delta).isoformat(),
            correlation_id=str(UUID(int=command_id + 1)),
            preconditions={},
        )

    def test_duplicate_command_has_one_terminal_event_and_safe_final_state(self) -> None:
        command = self.command()
        first = self.server.submit_command(command)
        second = self.server.submit_command(command)
        self.assertIs(first, second)
        self.assertEqual(len(self.server.events_after("0")), 1)
        self.assertTrue(self.server.driver.stopped)
        pose = Pose.from_dict(self.server.events_after("0")[0].payload["pose"])
        self.assertEqual(pose.frame_id, "urn:sap:frame:agent:simulation:r2:odom")
        self.assertEqual(len(pose.covariance_6x6 or ()), 36)
        self.assertEqual(pose.source, "deterministic_simulator_truth")

    def test_stale_command_is_rejected_and_final_state_is_safe(self) -> None:
        status = self.server.submit_command(self.command(stale=True))
        self.assertEqual(status.state, "rejected")
        self.assertEqual(status.reason_code, "sap.command_stale")
        self.assertTrue(self.server.driver.stopped)
        self.assertEqual(status.result, {"safe_state": "safe_hold"})

    def test_cursor_resume_is_ordered_and_excludes_delivered_events(self) -> None:
        self.server.submit_command(self.command(command_id=100, key="a"))
        self.server.submit_command(self.command(command_id=200, key="b"))
        resumed = self.server.events_after("1")
        self.assertEqual([event.sequence for event in resumed], [2])

    def test_restart_never_reconstructs_motion(self) -> None:
        restarted = SimAgentServer(seed=7)
        self.assertTrue(restarted.driver.stopped)
        self.assertEqual(restarted.events_after("0"), ())

    def test_missing_capability_fails_negotiation(self) -> None:
        with self.assertRaisesRegex(ValueError, "sap.capability_missing"):
            self.server.create_session(
                SessionRequest(
                    peer_id="urn:sap:provider:test",
                    protocol_versions=("0.1.0",),
                    required_capabilities=("command.move_relative",),
                    requested_duration_s=30,
                )
            )


if __name__ == "__main__":
    unittest.main()
