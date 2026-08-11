from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class DroidDriver(Protocol):
    def safe_hold(self) -> None: ...


class HardwareUnavailableError(RuntimeError):
    pass


class Spherov2R2Driver:
    """Phase 1 adapter seam; deliberately impossible to instantiate in P0."""

    def __init__(self) -> None:
        raise HardwareUnavailableError(
            "Spherov2R2Driver is unavailable in Phase 0; simulation is mandatory"
        )


@dataclass
class SimDroidDriver:
    """A deterministic driver with no BLE or hardware code path."""

    stopped: bool = True
    history: list[str] = field(default_factory=list)

    def safe_hold(self) -> None:
        self.stopped = True
        self.history.append("safe_hold")
