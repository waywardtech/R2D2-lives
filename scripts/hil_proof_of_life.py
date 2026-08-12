"""Separately armed, stationary R2 proof of life; no drive, heading, legs, or animations."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.encounters import allowed_audio_names
from r2_runtime.hil_preflight import validate_proof_of_life_preflight
from r2_runtime.proof_of_life import run_proof_of_life
from r2_runtime.recording import write_immutable_json
from r2_runtime.spherov2_backend import Spherov2LibraryBackend, StationaryProbePolicy
from r2_runtime.system_status import collect_system_status, merge_droid_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One stationary R2 proof of life with a complete system-state report"
    )
    parser.add_argument("--authorize-proof-of-life", action="store_true")
    parser.add_argument("--operator-present", action="store_true")
    parser.add_argument("--device-inspected", action="store_true")
    parser.add_argument("--temperature-ok", action="store_true")
    parser.add_argument("--keepout-clear", action="store_true")
    parser.add_argument("--emergency-stop-ready", action="store_true")
    parser.add_argument("--charging-safe-only", action="store_true")
    parser.add_argument("--second-go-confirmed", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        preflight = validate_proof_of_life_preflight(args, os.environ)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    seed = args.seed if args.seed is not None else secrets.randbits(32)
    policy = StationaryProbePolicy(
        allow_head_read=True,
        allow_stationary_expressions=True,
        allowed_audio_names=allowed_audio_names(),
    )
    backend = Spherov2LibraryBackend(policy=policy)
    driver = Spherov2R2Driver(backend=backend, configured_identity=preflight.identity)
    owner = BleOwner(driver)
    progress_path_raw = os.environ.get("R2_PROOF_OF_LIFE_PROGRESS_PATH")
    progress_path = Path(progress_path_raw) if progress_path_raw else None
    sequence = 0

    def mark(stage: str, detail: object) -> None:
        nonlocal sequence
        if progress_path is None:
            return
        sequence += 1
        record = {
            "sequence": sequence,
            "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "stage": stage,
            "detail": detail,
        }
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        with progress_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    try:
        payload = run_proof_of_life(owner, driver, seed=seed, stage_sink=mark).to_dict()
    except Exception as error:
        droid = {
            "connection": owner.state.value,
            "safe_hold": driver.stopped,
            "movement_performed": False,
            "expression": {
                "status": "failed",
                "error_type": type(error).__name__,
                "error_stage": getattr(error, "phase", None),
            },
        }
        payload = {
            "schema_version": "1.0",
            "evidence_category": "stationary-proof-of-life-failure",
            "seed": seed,
            "status": merge_droid_snapshot(collect_system_status(), droid),
            "final_state": owner.state.value,
            "movement_performed": False,
        }
        digest = write_immutable_json(args.output, payload)
        print(
            json.dumps({"terminal": "failed", "report_sha256": digest, **payload}, sort_keys=True)
        )
        raise SystemExit(2) from None
    digest = write_immutable_json(args.output, payload)
    print(json.dumps({"terminal": "completed", "report_sha256": digest, **payload}, sort_keys=True))


if __name__ == "__main__":
    main()
