from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class SpatialProviderClient(Protocol):
    def state(self) -> str: ...


@dataclass(frozen=True)
class NullSpatialProviderClient:
    def state(self) -> str:
        return "unavailable"


@dataclass(frozen=True)
class SimSpatialProviderClient:
    seed: int = 20260811

    def state(self) -> str:
        return "simulation"


@dataclass(frozen=True)
class SapSpatialProviderClient:
    """Transport-injected SAP adapter; network transport arrives after P0."""

    endpoint: str
    request: Callable[[str, dict[str, Any]], dict[str, Any]]

    def state(self) -> str:
        response = self.request(f"{self.endpoint}/v1/health", {})
        return str(response.get("status", "unavailable"))


def select_spatial_provider(name: str) -> SpatialProviderClient:
    if name == "null":
        return NullSpatialProviderClient()
    if name == "sim":
        return SimSpatialProviderClient()
    raise ValueError(f"unsupported spatial provider: {name}")
