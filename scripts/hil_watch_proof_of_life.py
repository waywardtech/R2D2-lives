"""Explicit external watchdog for one separately authorized proof-of-life run."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.proof_watchdog import (  # noqa: E402
    supervise_proof_process,
    validate_proof_watchdog_authorization,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bound one stationary proof-of-life HIL child")
    parser.add_argument("--authorize-watchdog-run", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=75.0)
    args = parser.parse_args()
    try:
        validate_proof_watchdog_authorization(
            authorized=args.authorize_watchdog_run,
            arm_token=os.environ.get("R2_PROOF_WATCHDOG_TOKEN"),
            timeout_s=args.timeout_seconds,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    result = supervise_proof_process(
        [sys.executable, os.fspath(ROOT / "scripts" / "hil_launch_proof_of_life.py")],
        timeout_s=args.timeout_seconds,
        progress_path=ROOT / "proof-of-life-progress.jsonl",
        watchdog_evidence_path=ROOT / "proof-of-life-watchdog.json",
        reserved_paths=(ROOT / "proof-of-life-live.json",),
    )
    print(json.dumps(result.__dict__, sort_keys=True))
    raise SystemExit(124 if result.timed_out else result.child_returncode)


if __name__ == "__main__":
    main()
