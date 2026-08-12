"""External process watchdog for the separately armed stationary encounter HIL."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import subprocess

from .encounter_progress import build_encounter_watchdog_evidence, read_encounter_progress
from .recording import write_immutable_json

ENCOUNTER_WATCHDOG_ARM_TOKEN = "AUTHORIZE_WATCHDOG_STATIONARY_ENCOUNTER"


@dataclass(frozen=True)
class EncounterWatchdogResult:
    timed_out: bool
    child_returncode: int | None
    evidence_sha256: str | None


def validate_encounter_watchdog_authorization(
    *, authorized: bool, arm_token: str | None, timeout_s: float
) -> None:
    """Refuse before child construction unless both gates and bounds are exact."""

    if not authorized:
        raise ValueError("stationary encounter watchdog is disabled without explicit authorization")
    if arm_token != ENCOUNTER_WATCHDOG_ARM_TOKEN:
        raise ValueError("missing exact external encounter watchdog arm token")
    if not 20.0 <= timeout_s <= 120.0:
        raise ValueError("watchdog timeout must be in [20, 120] seconds")


def supervise_encounter_process(
    command: Sequence[str],
    *,
    timeout_s: float,
    progress_path: Path,
    watchdog_evidence_path: Path,
    termination_grace_s: float = 5.0,
    reserved_paths: Sequence[Path] = (),
) -> EncounterWatchdogResult:
    """Run one fixed HIL child and preserve classified evidence if it exceeds its bound."""

    if not command:
        raise ValueError("watchdog command must not be empty")
    if timeout_s <= 0 or termination_grace_s <= 0:
        raise ValueError("watchdog bounds must be positive")
    if any(path.exists() for path in (progress_path, watchdog_evidence_path, *reserved_paths)):
        raise FileExistsError("refusing to reuse encounter watchdog evidence paths")

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
        journal_present = progress_path.is_file()
        markers = read_encounter_progress(progress_path) if journal_present else ()
        evidence = build_encounter_watchdog_evidence(markers, journal_present=journal_present)
        digest = write_immutable_json(watchdog_evidence_path, evidence)
        return EncounterWatchdogResult(True, None, digest)
    return EncounterWatchdogResult(False, returncode, None)
