"""Explicit external watchdog for one separately authorized stationary encounter run."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.encounter_watchdog import (  # noqa: E402
    supervise_encounter_process,
    validate_encounter_watchdog_authorization,
)

PROGRESS = ROOT / "encounter-progress.jsonl"
WATCHDOG_EVIDENCE = ROOT / "encounter-watchdog.json"
LIVE_EVIDENCE = ROOT / "encounter-live.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Bound one stationary encounter HIL child")
    parser.add_argument("--authorize-watchdog-run", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=40.0)
    args = parser.parse_args()
    try:
        validate_encounter_watchdog_authorization(
            authorized=args.authorize_watchdog_run,
            arm_token=os.environ.get("R2_ENCOUNTER_WATCHDOG_TOKEN"),
            timeout_s=args.timeout_seconds,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    result = supervise_encounter_process(
        [sys.executable, os.fspath(ROOT / "scripts" / "hil_launch_single_r2_encounter.py")],
        timeout_s=args.timeout_seconds,
        progress_path=PROGRESS,
        watchdog_evidence_path=WATCHDOG_EVIDENCE,
        reserved_paths=(LIVE_EVIDENCE,),
    )
    print(json.dumps(result.__dict__, sort_keys=True))
    if result.timed_out:
        raise SystemExit(124)
    raise SystemExit(result.child_returncode)


if __name__ == "__main__":
    main()
