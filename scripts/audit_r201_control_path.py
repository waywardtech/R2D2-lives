"""Compare the reviewed R201 diagnostic path with pinned upstream bindings.

This audit reads source text only. It never imports the vendor package or opens
Bluetooth, so it is safe for CI and target-host staging.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _require(path: Path, marker: str) -> None:
    if marker not in path.read_text(encoding="utf-8"):
        raise ValueError(f"pinned source drift: {path.name} lacks required binding")


def audit(vendor_root: Path, backend_path: Path) -> dict[str, object]:
    r2d2 = vendor_root / "toy" / "r2d2.py"
    bb9e = vendor_root / "toy" / "bb9e.py"
    drive = vendor_root / "commands" / "drive.py"
    for path in (r2d2, bb9e, drive, backend_path):
        if not path.is_file():
            raise ValueError(f"required source is missing: {path}")

    _require(r2d2, "generic_raw_motor = Drive.generic_raw_motor")
    _require(bb9e, "set_raw_motors = Drive.set_raw_motors")
    _require(bb9e, "drive_with_heading = Drive.drive_with_heading")
    _require(
        drive,
        "def set_raw_motors(toy, left_mode: RawMotorModes, left_speed, right_mode: RawMotorModes, right_speed, proc=None):",
    )
    _require(
        drive, "def drive_with_heading(toy, speed, heading, drive_flags: DriveFlags, proc=None):"
    )
    _require(
        drive,
        "def generic_raw_motor(toy, index: GenericRawMotorIndexes, mode: GenericRawMotorModes, speed, proc=None):",
    )
    backend_text = backend_path.read_text(encoding="utf-8")
    secondary_uses = backend_text.count("processors.Processors.SECONDARY")
    if secondary_uses < 3:
        raise ValueError("diagnostic source no longer identifies its secondary-processor path")

    reviewed = (r2d2, bb9e, drive, backend_path)
    return {
        "schema_version": "1.0",
        "hardware_accessed": False,
        "movement_performed": False,
        "upstream_stock_r2_drive_processor": "default_primary",
        "diagnostic_drive_processor": "secondary",
        "control_path_differences_count": 2,
        "differences": [
            "stock R2 raw-motor and heading bindings retain proc=None",
            "reviewed diagnostic explicitly targets Processors.SECONDARY",
        ],
        "reviewed_source_sha256": {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in reviewed
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vendor-root", required=True, type=Path)
    parser.add_argument("--backend", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.vendor_root, args.backend)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(serialized, end="")
    else:
        if args.output.exists():
            raise SystemExit("refusing to overwrite an existing audit output")
        args.output.write_text(serialized, encoding="utf-8")
        print(json.dumps({"report_sha256": hashlib.sha256(serialized.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
