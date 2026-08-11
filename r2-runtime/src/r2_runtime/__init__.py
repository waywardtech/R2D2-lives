"""R2 Runtime public exports, loaded lazily to preserve adapter isolation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import R2Config
    from .sim_agent import SimAgentServer

__all__ = ["R2Config", "SimAgentServer"]


def __getattr__(name: str) -> Any:
    if name == "R2Config":
        from .config import R2Config

        return R2Config
    if name == "SimAgentServer":
        from .sim_agent import SimAgentServer

        return SimAgentServer
    raise AttributeError(name)
