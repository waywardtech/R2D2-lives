"""Deterministic low-level backend for Phase 1 adapter tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class SimSpherov2Backend:
    seed: int = 20260811
    library_version: str = "0.12.1"
    connected: bool = False
    stopped: bool = True
    calls: list[str] = field(default_factory=list)

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
