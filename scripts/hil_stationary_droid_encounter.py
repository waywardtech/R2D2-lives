"""Explicitly armed, charging-safe R2 reaction to nearby droid advertisements."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.encounter_session import run_droid_encounter_session
from r2_runtime.encounter_progress import DurableEncounterProgress
from r2_runtime.encounters import DroidEncounterChat, allowed_audio_names
from r2_runtime.hil_preflight import validate_stationary_encounter_preflight
from r2_runtime.recording import build_hil_failure_evidence, write_immutable_json
from r2_runtime.spherov2_backend import Spherov2LibraryBackend, StationaryProbePolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stationary nearby-droid reaction; no drive, heading, leg, or animation calls"
    )
    parser.add_argument("--authorize-stationary-encounter", action="store_true")
    parser.add_argument("--operator-present", action="store_true")
    parser.add_argument("--device-inspected", action="store_true")
    parser.add_argument("--temperature-ok", action="store_true")
    parser.add_argument("--keepout-clear", action="store_true")
    parser.add_argument("--emergency-stop-ready", action="store_true")
    parser.add_argument("--charging-safe-only", action="store_true")
    parser.add_argument("--second-go-confirmed", action="store_true")
    parser.add_argument("--max-reactions", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260811)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        preflight = validate_stationary_encounter_preflight(args, os.environ)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    policy = StationaryProbePolicy(
        allow_stationary_expressions=True,
        allowed_audio_names=allowed_audio_names(),
    )
    backend = Spherov2LibraryBackend(policy=policy)
    driver = Spherov2R2Driver(backend=backend, configured_identity=preflight.identity)
    owner = BleOwner(driver)
    progress_path = os.environ.get("R2_ENCOUNTER_PROGRESS_PATH")
    progress = DurableEncounterProgress(Path(progress_path)) if progress_path else None
    stage_sink = progress.record if progress is not None else None
    try:
        report = run_droid_encounter_session(
            owner,
            driver,
            DroidEncounterChat(seed=args.seed),
            max_reactions=preflight.max_reactions,
            stage_sink=stage_sink,
        )
    except Exception as error:
        failure = build_hil_failure_evidence(
            error_type=type(error).__name__,
            owner_state=owner.state.value,
            driver_connected=driver.connected,
            driver_stopped=driver.stopped,
            error_stage=getattr(error, "phase", None),
        )
        digest = write_immutable_json(args.output, failure)
        print(
            json.dumps(
                {
                    "evidence_category": failure["evidence_category"],
                    "report_sha256": digest,
                    "movement_performed": False,
                    "terminal": "failed",
                },
                sort_keys=True,
            )
        )
        raise SystemExit(2) from None
    payload = report.to_dict()
    digest = write_immutable_json(args.output, payload)
    print(
        json.dumps(
            {
                "evidence_category": payload["evidence_category"],
                "observed_droid_kinds": payload["observed_droid_kinds"],
                "reaction_count": len(report.reactions),
                "report_sha256": digest,
                "movement_performed": False,
                "final_state": report.final_state,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
