"""Replaceable BSM seams required before acoustic implementation begins."""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence


class MicrophoneNode(Protocol):
    def capture(self, duration_s: float) -> bytes: ...


class ProbeSignal(Protocol):
    def metadata(self) -> Mapping[str, object]: ...


class ClockSynchronizer(Protocol):
    def quality(self) -> Mapping[str, object]: ...


class AcousticSolver(Protocol):
    def estimate(self, evidence_ids: Sequence[str]) -> Mapping[str, object]: ...


class WorldModelStore(Protocol):
    def publish_revision(self, manifest: Mapping[str, object]) -> str: ...
