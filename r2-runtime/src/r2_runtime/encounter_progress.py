"""Durable privacy-safe progress markers for watchdog-bounded encounter HIL."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Mapping

ALLOWED_STAGES = frozenset(
    {
        "scan_started",
        "scan_completed",
        "connect_started",
        "connect_completed",
        "battery_checked",
        "expression_started",
        "expression_completed",
        "disconnect_started",
        "disconnect_completed",
        "session_failed",
        "session_completed",
    }
)
ALLOWED_DETAIL_KEYS = frozenset({"droid_kind_count", "reaction_number", "battery_safe"})


@dataclass(frozen=True)
class EncounterProgressMarker:
    sequence: int
    stage: str
    detail: Mapping[str, object]


class DurableEncounterProgress:
    """Append-only JSONL with fsync; never accepts names, addresses, or exception text."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._sequence = self._load_sequence()

    def _load_sequence(self) -> int:
        if not self._path.exists():
            return 0
        markers = read_encounter_progress(self._path)
        return markers[-1].sequence if markers else 0

    def record(self, stage: str, detail: Mapping[str, object] | None = None) -> None:
        if stage not in ALLOWED_STAGES:
            raise ValueError("unsupported encounter progress stage")
        safe_detail = dict(detail or {})
        unknown = set(safe_detail) - ALLOWED_DETAIL_KEYS
        if unknown:
            raise ValueError(f"unsafe encounter progress detail keys: {sorted(unknown)}")
        self._sequence += 1
        marker = EncounterProgressMarker(self._sequence, stage, safe_detail)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(asdict(marker), sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())


def read_encounter_progress(path: Path) -> tuple[EncounterProgressMarker, ...]:
    markers: list[EncounterProgressMarker] = []
    for expected, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(line)
        if set(value) != {"sequence", "stage", "detail"} or value["sequence"] != expected:
            raise ValueError("invalid encounter progress sequence or shape")
        if value["stage"] not in ALLOWED_STAGES:
            raise ValueError("invalid encounter progress stage")
        detail = value["detail"]
        if not isinstance(detail, dict) or set(detail) - ALLOWED_DETAIL_KEYS:
            raise ValueError("invalid encounter progress detail")
        markers.append(EncounterProgressMarker(expected, value["stage"], detail))
    return tuple(markers)
