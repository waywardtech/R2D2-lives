"""External watchdog and privacy-safe timeout evidence for proof-of-life HIL."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess

from .recording import write_immutable_json

PROOF_WATCHDOG_ARM_TOKEN = "AUTHORIZE_WATCHDOG_STATIONARY_PROOF_OF_LIFE"

_STAGES = (
    "system_status_collected",
    "connect_started",
    "connect_completed",
    "identity_checked",
    "battery_checked",
    "head_checked",
    "expression_started",
    "expression_completed",
    "session_failed",
    "disconnect_started",
    "disconnect_completed",
    "session_completed",
)


@dataclass(frozen=True)
class ProofWatchdogResult:
    timed_out: bool
    child_returncode: int | None
    evidence_sha256: str | None


def validate_proof_watchdog_authorization(
    *, authorized: bool, arm_token: str | None, timeout_s: float
) -> None:
    if not authorized:
        raise ValueError("proof-of-life watchdog is disabled without explicit authorization")
    if arm_token != PROOF_WATCHDOG_ARM_TOKEN:
        raise ValueError("missing exact external proof-of-life watchdog arm token")
    if not 20.0 <= timeout_s <= 120.0:
        raise ValueError("watchdog timeout must be in [20, 120] seconds")


def _read_stages(path: Path) -> tuple[str, ...]:
    stages: list[str] = []
    for expected, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(line)
        if set(value) != {"sequence", "occurred_at", "stage", "detail"}:
            raise ValueError("invalid proof-of-life progress shape")
        if value["sequence"] != expected or value["stage"] not in _STAGES:
            raise ValueError("invalid proof-of-life progress sequence or stage")
        if not isinstance(value["occurred_at"], str) or not isinstance(value["detail"], dict):
            raise ValueError("invalid proof-of-life progress value")
        if set(value["detail"]) - {"battery_safe"}:
            raise ValueError("unsafe proof-of-life progress detail")
        stages.append(value["stage"])
    return tuple(stages)


def _classification(stages: tuple[str, ...]) -> str:
    if not stages:
        return "no_progress"
    return {
        "system_status_collected": "connection_start_stalled",
        "connect_started": "connection_stalled",
        "connect_completed": "identity_query_stalled",
        "identity_checked": "battery_query_stalled",
        "battery_checked": "head_query_stalled",
        "head_checked": "expression_start_stalled",
        "expression_started": "expression_execution_stalled",
        "expression_completed": "ready_or_disconnect_stalled",
        "session_failed": "disconnect_start_stalled",
        "disconnect_started": "disconnect_stalled",
        "disconnect_completed": "final_report_stalled",
        "session_completed": "completed",
    }[stages[-1]]


def supervise_proof_process(
    command: Sequence[str],
    *,
    timeout_s: float,
    progress_path: Path,
    watchdog_evidence_path: Path,
    termination_grace_s: float = 5.0,
    reserved_paths: Sequence[Path] = (),
) -> ProofWatchdogResult:
    if not command or timeout_s <= 0 or termination_grace_s <= 0:
        raise ValueError("watchdog command and bounds must be valid")
    if any(path.exists() for path in (progress_path, watchdog_evidence_path, *reserved_paths)):
        raise FileExistsError("refusing to reuse proof-of-life watchdog evidence paths")
    process = subprocess.Popen(tuple(command))
    try:
        returncode = process.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=termination_grace_s)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        present = progress_path.is_file()
        stages = _read_stages(progress_path) if present else ()
        payload = {
            "schema_version": "1.0",
            "evidence_category": "stationary-proof-of-life-watchdog",
            "terminal": "watchdog_timeout",
            "stall_classification": _classification(stages),
            "last_durable_stage": stages[-1] if stages else None,
            "marker_count": len(stages),
            "journal_integrity": "verified" if present else "absent",
            "process_terminated": True,
            "ble_disconnect_verified": "disconnect_completed" in stages,
            "operator_state_confirmation_required": True,
            "movement_performed": False,
            "device_identity_persisted": False,
        }
        digest = write_immutable_json(watchdog_evidence_path, payload)
        return ProofWatchdogResult(True, None, digest)
    return ProofWatchdogResult(False, returncode, None)
