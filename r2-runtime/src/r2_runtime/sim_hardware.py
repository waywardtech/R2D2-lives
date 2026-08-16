"""Deterministic low-level backend for Phase 1 adapter tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .encounters import StationaryExpressionPlan


@dataclass
class SimSpherov2Backend:
    seed: int = 20260811
    library_version: str = "0.12.1"
    connected: bool = False
    stopped: bool = True
    calls: list[str] = field(default_factory=list)
    nearby_droids: tuple[str, ...] = ("bb8",)

    def connect(self, configured_identity: str) -> None:
        if configured_identity != "D2-SIMULATED":
            raise RuntimeError("simulated identity mismatch")
        self.connected = True
        self.stopped = True
        self.calls.append("connect")

    def disconnect(self) -> None:
        self.connected = False
        self.stopped = True
        self.calls.append("disconnect")

    def stop(self) -> None:
        self.stopped = True
        self.calls.append("stop")

    def dispatch_stop_no_wait(self) -> None:
        self.stopped = True
        self.calls.append("stop_no_wait")

    def dispatch_bounded_forward_no_wait(self, speed: int) -> None:
        self.stopped = False
        self.calls.append(f"forward_no_wait:{speed}")

    def dispatch_heading_forward_no_wait(self, speed: int, heading_degrees: int = 0) -> None:
        self.stopped = False
        self.calls.append(f"heading_forward_no_wait:{speed}:{heading_degrees}")

    def identity(self) -> Mapping[str, str]:
        self.calls.append("identity")
        return {"model": "R201-sim", "system": "sim-system-1", "firmware": "sim-fw-1"}

    def battery(self) -> Mapping[str, object]:
        self.calls.append("battery")
        return {"state": "ok", "voltage_v": 3.8, "provenance": "simulation"}

    def exercise_stationary(self, capability: str) -> Mapping[str, object]:
        if capability.startswith(("drive.", "stop.latency", "locator.motion")):
            raise AssertionError("stationary probe attempted movement capability")
        self.calls.append(capability)
        return {"result": "simulated", "seed": self.seed}

    def discover_nearby_droids(self, configured_identity: str) -> tuple[str, ...]:
        self.calls.append("discover_nearby_droids")
        return self.nearby_droids

    def perform_stationary_expression(self, plan: StationaryExpressionPlan) -> None:
        if any(abs(position) > 20.0 for position in plan.head_positions_deg):
            raise AssertionError("simulated stationary expression exceeded head bound")
        self.calls.extend(
            (
                f"expression:{plan.semantic}",
                f"audio:{plan.audio_name}",
                *(f"led:{brightness}" for brightness in plan.logic_display_pattern),
                *(f"head:{position}" for position in plan.head_positions_deg),
                "expression_restored",
            )
        )
