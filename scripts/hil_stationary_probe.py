"""Separately marked, stationary-only R201 capability probe.

This script never enables movement. Every missing preflight or authorization
condition exits before constructing the BLE backend.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))
sys.path.insert(0, str(ROOT / "protocol" / "src"))

from r2_runtime.ble_owner import BleOwner
from r2_runtime.capability_probe import StationaryCapabilityProbe
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.hil_preflight import validate_stationary_preflight
from r2_runtime.recording import write_immutable_json
from r2_runtime.spherov2_backend import Spherov2LibraryBackend, StationaryProbePolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stationary R201 capability probe (movement is impossible from this command)"
    )
    parser.add_argument("--authorize-stationary-hil", action="store_true")
    parser.add_argument("--operator-present", action="store_true")
    parser.add_argument("--device-inspected", action="store_true")
    parser.add_argument("--temperature-ok", action="store_true")
    parser.add_argument("--keepout-clear", action="store_true")
    parser.add_argument("--emergency-stop-ready", action="store_true")
    parser.add_argument("--allow-led-preview", action="store_true")
    parser.add_argument("--allow-head-read", action="store_true")
    parser.add_argument("--allow-audio-preview", action="store_true")
    parser.add_argument("--audio-id", type=int)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        identity = validate_stationary_preflight(args, os.environ)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    policy = StationaryProbePolicy(
        allow_led_preview=args.allow_led_preview,
        allow_head_read=args.allow_head_read,
        allow_audio_preview=args.allow_audio_preview,
        audio_id=args.audio_id,
    )
    backend = Spherov2LibraryBackend(policy=policy)
    driver = Spherov2R2Driver(backend=backend, configured_identity=identity)
    report = StationaryCapabilityProbe(BleOwner(driver), driver).run(
        evidence_category="HIL-stationary"
    )
    digest = write_immutable_json(args.output, report.to_dict())
    print(
        json.dumps(
            {
                "evidence_category": report.evidence_category,
                "report_sha256": digest,
                "movement_performed": report.movement_performed,
                "final_state": report.final_state,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
