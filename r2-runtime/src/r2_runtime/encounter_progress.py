"""Durable privacy-safe progress markers for watchdog-bounded encounter HIL."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Iterable, Mapping

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

_EMPTY_DETAIL_STAGES = ALLOWED_STAGES - {
    "scan_completed",
    "battery_checked",
    "expression_started",
    "expression_completed",
}


@dataclass(frozen=True)
class EncounterProgressMarker:
    sequence: int
    stage: str
    detail: Mapping[str, object]


def _validate_detail(stage: str, detail: Mapping[str, object]) -> None:
    if stage in _EMPTY_DETAIL_STAGES:
        valid = not detail
    elif stage == "scan_completed":
        count = detail.get("droid_kind_count")
        valid = set(detail) == {"droid_kind_count"} and type(count) is int and 0 <= count <= 4
    elif stage == "battery_checked":
        valid = set(detail) == {"battery_safe"} and type(detail.get("battery_safe")) is bool
    else:
        number = detail.get("reaction_number")
        valid = set(detail) == {"reaction_number"} and type(number) is int and 1 <= number <= 5
    if not valid:
        raise ValueError("invalid encounter progress detail for stage")


def _reaction_number(marker: EncounterProgressMarker) -> int:
    value = marker.detail["reaction_number"]
    if type(value) is not int:
        raise ValueError("invalid encounter reaction number")
    return value


def validate_encounter_progress(markers: Iterable[EncounterProgressMarker]) -> None:
    """Validate a complete or watchdog-truncated encounter state-machine prefix."""

    previous: EncounterProgressMarker | None = None
    failed = False
    for expected_sequence, marker in enumerate(markers, 1):
        if marker.sequence != expected_sequence or marker.stage not in ALLOWED_STAGES:
            raise ValueError("invalid encounter progress sequence or stage")
        if not isinstance(marker.detail, Mapping):
            raise ValueError("invalid encounter progress detail")
        _validate_detail(marker.stage, marker.detail)
        if previous is None:
            if marker.stage != "scan_started":
                raise ValueError("invalid encounter progress initial stage")
        else:
            allowed_next: set[str]
            if previous.stage == "scan_started":
                allowed_next = {"scan_completed"}
            elif previous.stage == "scan_completed":
                allowed_next = (
                    {"session_completed"}
                    if previous.detail["droid_kind_count"] == 0
                    else {"connect_started"}
                )
            elif previous.stage == "connect_started":
                allowed_next = {"connect_completed", "session_failed"}
            elif previous.stage == "connect_completed":
                allowed_next = {"battery_checked", "session_failed"}
            elif previous.stage == "battery_checked":
                allowed_next = (
                    {"expression_started", "session_failed"}
                    if previous.detail["battery_safe"] is True
                    else {"session_failed"}
                )
            elif previous.stage == "expression_started":
                allowed_next = {"expression_completed", "session_failed"}
                if marker.stage == "expression_completed" and (
                    _reaction_number(marker) != _reaction_number(previous)
                ):
                    raise ValueError("mismatched encounter reaction number")
            elif previous.stage == "expression_completed":
                allowed_next = {"disconnect_started", "session_failed"}
                if _reaction_number(previous) < 5:
                    allowed_next.add("expression_started")
                if marker.stage == "expression_started" and (
                    _reaction_number(marker) != _reaction_number(previous) + 1
                ):
                    raise ValueError("nonconsecutive encounter reaction number")
            elif previous.stage == "session_failed":
                allowed_next = {"disconnect_started"}
            elif previous.stage == "disconnect_started":
                allowed_next = {"disconnect_completed"}
            elif previous.stage == "disconnect_completed":
                allowed_next = set() if failed else {"session_completed"}
            else:
                allowed_next = set()
            if marker.stage not in allowed_next:
                raise ValueError("invalid encounter progress stage transition")
        failed = failed or marker.stage == "session_failed"
        previous = marker


def classify_encounter_stall(markers: Iterable[EncounterProgressMarker]) -> str:
    """Classify the operation after the last durable marker without using identities."""

    snapshot = tuple(markers)
    validate_encounter_progress(snapshot)
    if not snapshot:
        return "no_progress"
    last = snapshot[-1]
    if last.stage == "scan_started":
        return "scan_stalled"
    if last.stage == "scan_completed":
        return (
            "finalization_stalled"
            if last.detail["droid_kind_count"] == 0
            else "connection_start_stalled"
        )
    classifications = {
        "connect_started": "connection_stalled",
        "connect_completed": "battery_query_stalled",
        "expression_started": "expression_execution_stalled",
        "expression_completed": "expression_loop_or_cleanup_stalled",
        "session_failed": "disconnect_start_stalled",
        "disconnect_started": "disconnect_stalled",
        "session_completed": "completed",
    }
    if last.stage == "battery_checked":
        return (
            "expression_planning_stalled"
            if last.detail["battery_safe"] is True
            else "failure_recording_stalled"
        )
    if last.stage == "disconnect_completed":
        failed = any(marker.stage == "session_failed" for marker in snapshot)
        return "failure_report_stalled" if failed else "final_report_stalled"
    return classifications[last.stage]


def build_encounter_watchdog_evidence(
    markers: Iterable[EncounterProgressMarker], *, journal_present: bool = True
) -> dict[str, object]:
    """Build deterministic, identity-free evidence after an external watchdog timeout."""

    snapshot = tuple(markers)
    stall = classify_encounter_stall(snapshot)
    completed_reactions = sum(marker.stage == "expression_completed" for marker in snapshot)
    return {
        "schema_version": "1.0",
        "evidence_category": "stationary-droid-encounter-watchdog",
        "terminal": "watchdog_timeout",
        "stall_classification": stall,
        "last_durable_stage": snapshot[-1].stage if snapshot else None,
        "marker_count": len(snapshot),
        "completed_reactions": completed_reactions,
        "journal_integrity": "verified" if journal_present else "absent",
        "movement_performed": False,
        "device_identity_persisted": False,
    }


class DurableEncounterProgress:
    """Append-only JSONL with fsync; never accepts names, addresses, or exception text."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._markers = self._load_markers()
        self._sequence = self._markers[-1].sequence if self._markers else 0

    def _load_markers(self) -> tuple[EncounterProgressMarker, ...]:
        if not self._path.exists():
            return ()
        return read_encounter_progress(self._path)

    def record(self, stage: str, detail: Mapping[str, object] | None = None) -> None:
        if stage not in ALLOWED_STAGES:
            raise ValueError("unsupported encounter progress stage")
        safe_detail = dict(detail or {})
        unknown = set(safe_detail) - ALLOWED_DETAIL_KEYS
        if unknown:
            raise ValueError(f"unsafe encounter progress detail keys: {sorted(unknown)}")
        _validate_detail(stage, safe_detail)
        marker = EncounterProgressMarker(self._sequence + 1, stage, safe_detail)
        validate_encounter_progress((*self._markers, marker))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(asdict(marker), sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self._sequence = marker.sequence
        self._markers = (*self._markers, marker)


def read_encounter_progress(path: Path) -> tuple[EncounterProgressMarker, ...]:
    markers: list[EncounterProgressMarker] = []
    for expected, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(line)
        if set(value) != {"sequence", "stage", "detail"} or value["sequence"] != expected:
            raise ValueError("invalid encounter progress sequence or shape")
        if not isinstance(value["stage"], str) or value["stage"] not in ALLOWED_STAGES:
            raise ValueError("invalid encounter progress stage")
        detail = value["detail"]
        if not isinstance(detail, dict) or set(detail) - ALLOWED_DETAIL_KEYS:
            raise ValueError("invalid encounter progress detail")
        markers.append(EncounterProgressMarker(expected, value["stage"], detail))
    snapshot = tuple(markers)
    validate_encounter_progress(snapshot)
    return snapshot
