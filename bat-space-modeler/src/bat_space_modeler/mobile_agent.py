from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from sap_protocol.generated import AgentClient, CommandRequest, CommandStatus, EventEnvelope, SessionRequest, SessionResponse


class MobileAgentClient(Protocol):
    def capabilities(self) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class SimMobileAgentClient:
    seed: int = 20260811

    def capabilities(self) -> tuple[str, ...]:
        return ("command.stop", "command.safe_hold", "command.hold_pose")


@dataclass(frozen=True)
class SapMobileAgentClient:
    """Generic adapter over a generated SAP AgentClient implementation."""

    client: AgentClient

    def capabilities(self) -> tuple[str, ...]:
        return ("negotiated_via_session",)

    def create_session(self, request: SessionRequest) -> SessionResponse:
        return self.client.create_session(request)

    def submit_command(self, request: CommandRequest) -> CommandStatus:
        return self.client.submit_command(request)

    def events_after(self, cursor: str) -> tuple[EventEnvelope, ...]:
        return self.client.events_after(cursor)


def select_mobile_agent(name: str) -> MobileAgentClient:
    if name == "sim":
        return SimMobileAgentClient()
    raise ValueError("Phase 0 supports only the generic simulation mobile agent")
